'''This is a testing script for choropleth_objects'''
from choroshape import *
from choroshape.choroshape import round_py2
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import us
import ast
import io
import zipfile
from six import string_types
import pytest
import json
import re

try:
    import urllib.request as urllib  # Python3
except ImportError:
    import urllib  # Python2


#Let's start by making some datasets for global testing using the ACS API
mytoken =  # put your token here
OUTPATH = os.path.expanduser('~/Desktop/Example_Files/')


def make_url(table_code, mytoken=mytoken):
    '''Makes an url to use as a call for the 2014 5-year ACS API'''
    url = 'http://api.census.gov/data/2014/acs5?get=NAME,%s&for=county:*&in=state:*&key=%s' % (
        table_code, mytoken)
    return url


def census_call(url, table_code, label='category'):
    '''Calls a table from the census API and creates a pandas DataFrame
    Args:
        url(str): complete url to use for the call, alread has the table_code.
            Examples can be found ont the Census API guide.
        table_code(str): the table code for the table being called
        label(str): a more descriptive label for the table
    Returns:
        df(pd.DataFrame): data in DataFrame format'''
    response = urllib.urlopen(url)
    # data = response.read()
    str_response = response.read().decode('utf-8')
    data = json.loads(str_response)
    df = pd.DataFrame(data[1:], columns=data[0]).rename(columns={table_code: label})
    return df


@pytest.fixture(scope="module")
def create_totaldf():
    total_code = 'B01001_001E'
    total_url = make_url(total_code)
    return census_call(total_url, total_code, 'total_pop').iloc[:, 1:]


# Creates a dict for storing the DataFrames
@pytest.fixture(scope="module")
def create_data_dict(create_totaldf):
    '''Pulls data from the census and returns a dict of dataframes'''
    df_total = create_totaldf
    # Creates a total dataframe first
    table_dict = {'B01001_037E': 'Female: 35 to 39 years',
                  'B05001_005E': 'U.S. citizen by naturalization',
                  'B06008_002E': 'Never married'}
    df_dict = {}
    for key in table_dict:
        url = make_url(key)
        label = table_dict[key]
        df = census_call(url, key, label)
        # Merges with the total df
        df = pd.merge(df_total, df, how='inner', on=['state', 'county'])
        df = df[['NAME', 'state', 'county', label, 'total_pop']]
        df[label] = df[label].astype(float)
        df['total_pop'] = df['total_pop'].astype(float)
        # Creates a proportion for later testing
        df['ratio'] = df[label]/df['total_pop']
        # store the df in the dict and now we have some df's for testing!
        df = fix_FIPS(df, 'county', 'state')
        df_dict[label] = df
    return df_dict


# Used this bit to download shapefiles from Tiger
@pytest.fixture(scope="module")
def create_shape_files():
    states = ['MA', 'MI', 'CA', 'CO', 'NY', 'MD']
    shapefile_lookups = {}
    for state in states:
        methodToCall = getattr(us.states, state)
        shpurl = methodToCall.shapefile_urls()['county']
        remotezip = urllib.urlopen(shpurl)
        zipinmemory = io.BytesIO(remotezip.read())
        z = zipfile.ZipFile(zipinmemory)
        fn_path = '%stesting/shapefiles/' % OUTPATH
        dirname = os.path.normpath(fn_path)
        z.extractall(dirname)
        fn = next(fn for fn in z.namelist() if fn.endswith('.shp'))
        fn = os.path.normpath(fn_path + fn)
        shapefile_lookups[state] = fn
    return shapefile_lookups


def test_round_py2():
    assert round_py2(1.5) == 2
    assert round_py2(1.3) == 1
    assert round_py2(2.5) == 3
    assert round_py2(2.6) == 3
    assert round_py2(1.5, 1) == 1.5


def test_fips_noerr():
    col = 'fips'
    state_fips_list = ['25', ' 25', 25]
    data = pd.DataFrame.from_dict({col: [
        '001', ' 002', 103,  25004, '25005', '25-008',
        '25.009', 10]})
    for s in state_fips_list:
        fixed_data = fix_FIPS(data, col, s)
        for x in fixed_data[col]:
            assert isinstance(x, string_types)
            assert len(x) == 5
            assert x[0:2] == '25'


def test_fips_valerr():
    col = 'fips'
    state_fips = '25'
    list_by_error = {
        None: 'empty', 'bb007': 'non-digit', 2500007: '5-digit'}
    for val in list_by_error.keys():
        msg = list_by_error[val]
        data = pd.DataFrame.from_dict({col: ['25001', '35003', val]})
        with pytest.raises(ValueError) as excinfo:
            fix_FIPS(data, col, state_fips)
        assert msg in str(excinfo.value)


def test_get_custom_bins_noerr():
    levels = [1, .4, 2, 20]
    difs = [.6, .1, .0002]
    num_cats = [20, 6, 5]
    directions = [None, 'pos', 'neutral']
    for level in levels:
        for dif in difs:
            for num in num_cats:
                for direction in directions:
                    x = get_custom_bins(level, num, dif, direction)
                    assert isinstance(x, list)
                    assert x == sorted(x)
                    assert len(x) == num + 1
                    if dir == 'pos':
                        assert level == x[1]
                    # else:
                    #     assert level == x[int(round(float(num)/2))]


def test_get_custom_bins_valerr():
    with pytest.raises(ValueError) as excinfo:
        get_custom_bins(0)
    assert 'less than or equal to zero' in str(excinfo.value)


def test_area_pop_data(create_data_dict, create_shape_files, create_totaldf):
    FIPS_col = 'FIPS'
    geoFIPS_col = 'FIPS'
    for state, fn in create_shape_files.items():
        geodf = gpd.GeoDataFrame.from_file(fn)
        geodf = fix_FIPS(geodf, 'COUNTYFP10', 'STATEFP10')
        for key, df in create_data_dict.items():
            # Scenario 1: Total col and cat col are passed
            # Ratio is calculated in object
            apd_postcalc = AreaPopDataset(df, geodf, FIPS_col, geoFIPS_col,
                                          cat_col=key, total_col='total_pop',
                                          footnote='Map Created by testing',
                                          cat_name=key, title=key,
                                          bins=[0, 25, 75, 100],
                                          precision=3)
            # Check that an AreaPopDataset object is returned
            assert isinstance(apd_postcalc, AreaPopDataset)
            # Check that the groups are working
            assert isinstance((apd_postcalc.data[
                apd_postcalc.data[apd_postcalc.grouped_col] == 1]),
                pd.DataFrame)

            # Scenario 2: Only a category col is passed, a ratio
            apd_precalc = AreaPopDataset(df, geodf, FIPS_col, geoFIPS_col,
                                         cat_col='ratio',
                                         footnote='Map Created by testing',
                                         cat_name=key, title=key,
                                         bins=[0, 25, 75, 100],
                                         precision=3)
            # Check that an AreaPopDataset object is returned
            assert isinstance(apd_precalc, AreaPopDataset)
            # Check that the groups are working
            assert isinstance((apd_precalc.data[
                apd_precalc.data[apd_precalc.grouped_col] == 1]),
                pd.DataFrame)


            # Check that the ratio is calculated correctly in Scenario 1
            assert np.allclose(apd_precalc.data['ratio'],
                               apd_postcalc.data['ratio'],
                               rtol=.00001, atol=.00001)

            # Scenario 3: Only a category col is passed, not a ratio
            apd = AreaPopDataset(df, geodf, FIPS_col, geoFIPS_col,
                                 cat_col=key,
                                 footnote='Map Created by testing',
                                 cat_name=key, title=key,
                                 bins=None,
                                 percent_format=False, precision=0)
            # Check that an AreaPopDataset object is returned
            assert isinstance(apd, AreaPopDataset)
            x = len((apd.data[apd.data[apd.grouped_col] == 1]).index)
            y = len((apd.data[apd.data[apd.grouped_col] == 4]).index)
            # Groups should be more or less equal
            assert abs(x-y) <= 5

            # Scenario 6: Have it calculate the bins alone
            apd = AreaPopDataset(df, geodf, FIPS_col, geoFIPS_col,
                                 cat_col=key, total_col='total_pop',
                                 footnote='Map Created by testing',
                                 cat_name=key, title=key,
                                 bins=None,
                                 num_cats=7)
            # Check that an AreaPopDataset object is returned
            assert isinstance(apd, AreaPopDataset)
            assert (len(apd.bins) == 8)
            x = len((apd.data[apd.data[apd.grouped_col] == 1]).index)
            y = len((apd.data[apd.data[apd.grouped_col] == 7]).index)
            # Groups should be more or less equal
            assert abs(x-y) <= 5

            # Scenario 6: Have it calculate the bins alone
            apd = AreaPopDataset(df, geodf, FIPS_col, geoFIPS_col,
                                 cat_col=key, total_col='total_pop',
                                 footnote='Map Created by testing',
                                 cat_name=key, title=key,
                                 bins=None,
                                 num_cats=20)
            # Check that an AreaPopDataset object is returned
            assert isinstance(apd, AreaPopDataset)
            # A lot of the bins will be overlapping in this case
            assert (len(apd.bins) <= 21)
            x = len((apd.data[apd.data[apd.grouped_col] == 1]).index)
            y = len((apd.data[apd.data[apd.grouped_col] == 7]).index)
            # Groups should be more or less equal
            assert abs(x-y) <= 10

        # Scenario 5: Only a total col is passed
        totaldf = fix_FIPS(create_totaldf, 'county', 'state')
        apd_total = AreaPopDataset(totaldf, geodf, FIPS_col, geoFIPS_col,
                                   total_col='total_pop',
                                   footnote='Map Created by testing',
                                   percent_format=False)
        # Check that an AreaPopDataset object is returned
        assert isinstance(apd_total, AreaPopDataset)
        x = len((apd.data[apd.data[apd.grouped_col] == 1]).index)
        y = len((apd.data[apd.data[apd.grouped_col] == 7]).index)
        # Groups should be more or less equal
        assert abs(x-y) <= 5


def test_make_choropleth(create_data_dict, create_shape_files):
    datafiles = {}
    for key, df in create_data_dict.items():
        name = re.sub('[^0-9a-zA-Z]+', '', key)
        df.columns = [
            'NAME', 'state', 'county', 'category', 'total', 'ratio', 'FIPS']
        df = df[['FIPS', 'category', 'total']]
        filename = os.path.normpath(
            '%stesting/datafiles/%s.csv' % (OUTPATH, name))
        df.to_csv(filename)
        datafiles[key] = filename
    for state, fn_state in create_shape_files.items():
        two_digit_state_FIPS = us.states.lookup(state).fips
        for key, fn_data in datafiles.items():
            make_choropleth(fn_data, fn_state, two_digit_state_FIPS,
                            title=key, footnote='Made for testing',
                            cat_name=name,
                            geoFIPS_col='COUNTYFP10', geometry_col=None)
