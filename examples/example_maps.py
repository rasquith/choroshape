'''This is a testing script for choropleth_objects
shape file comes from here" https://www.census.gov/geo/maps-data/data/cbf/cbf_counties.html'''
from choroshape import *
import datetime as dt
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import us
import json
import io
import zipfile

try:
    import urllib.request as urllib  # Python3
except ImportError:
    import urllib  # Python2

today = dt.datetime.today().strftime("%m/%d/%Y")
OUTPATH = os.path.expanduser('~/Desktop/Example_Files/')
mytoken = "acbb5df8ee5207bbdae91c2d8b878b4123011a90"


def census_call(url):
    '''Calls a table from the census API and creates a pandas DataFrame
    Args:
        url(str): complete url to use for the call, alread has the table_code.
            Examples can be found ont the Census API guide.
        table_code(str): the table code for the table being called
        label(str): a more descriptive label for the table
    Returns:
        df(pd.DataFrame): data in DataFrame format'''
    response = urllib.urlopen(url)
    str_response = response.read().decode('utf-8')
    data = json.loads(str_response)
    df = pd.DataFrame(data[1:], columns=data[0])
    return df



colors = 'blues'
size='large'
style_dict = {}
style_dict['MA'] = ChoroplethStyle(county_colors=colors, legx=.07, legy=0.18,
                                   ttl_align='left', ttlx=.08, ttly=0.9,
                                   ttl_char_limit=55, size=size)
style_dict['MI'] = ChoroplethStyle(county_colors=colors, legx=.07, legy=0.18,
                                   ttlx=.08, ttly=0.9, size=size)
style_dict['TX'] = ChoroplethStyle(county_colors=colors, legx=.07, legy=0.18,
                                   ttlx=.08, ttly=0.9)
style_dict['NC'] = ChoroplethStyle(county_colors=colors, legx=.07, legy=0.18,
                                   ttlx=.08, ttly=0.9)

style_dict['CO'] = ChoroplethStyle(county_colors=colors, legx=.07, legy=.12,
                                   ttlx=.08, ttly=0.84, size=size)

states = ['MA', 'MI', 'TX', 'CO', 'NC']
choropleth_dict = {}
for state in states:
    state_fips = us.states.lookup(state).fips
    state_name = us.states.lookup(state).name

    url = 'https://api.census.gov/data/2014/pep/cochar5?get=AGEGRP,RACE5,' +\
        'HISP,SEX,DATE,STNAME,POP&for=county:*&in=state' +\
        ':%s&key=%s' % (state_fips, mytoken)

    df = census_call(url)

    df = fix_FIPS(df, 'county', 'state')
    df['POP'] = df['POP'].str.strip().astype(int)
    df = df[df['DATE'] == '6']  # filter to 2014

    total = df[(df['AGEGRP'] == '0')]   # All ages
    total = total.groupby(['FIPS'], as_index=False).aggregate(np.sum)

    df = df[df['SEX'] == '2']  # Women
    df = df[(df['AGEGRP'] == '4') | (df['AGEGRP'] == '5') | (
        df['AGEGRP'] == '6') | (df['AGEGRP'] == '7') | (
        df['AGEGRP'] == '8') | (df['AGEGRP'] == '9') | (
        df['AGEGRP'] == '10')]  # 14 to 49

    df = df.groupby(['FIPS'], as_index=False).aggregate(np.sum)
    df.rename(columns={'POP': 'female_15_to_44'}, inplace=True)
    df = pd.merge(left=df, right=total, how='left', on='FIPS')
    df['ratio'] = df['female_15_to_44'].astype(float)/df['POP']
    
    remotezip = urllib.urlopen('http://www2.census.gov/geo/tiger/' +\
                               'GENZ2014/shp/cb_2014_us_county_500k.zip')
    zipinmemory = io.BytesIO(remotezip.read())
    z = zipfile.ZipFile(zipinmemory)
    fn_path = os.path.normpath('%stesting/shapefiles/' % OUTPATH)
    z.extractall(fn_path)
    bordersfn = os.path.join(fn_path, 'cb_2014_us_county_500k.shp')


    geodf = gpd.GeoDataFrame.from_file(bordersfn)
    geodf = (geodf[geodf['STATEFP'] == state_fips])

    geodf = fix_FIPS(geodf, 'COUNTYFP', 'STATEFP')

    footnote = 'Data Source: U.S. Census Bureau. (December 2015).\n    ' +\
               'Population Estimates and Projections.\n    ' +\
               'Retrieved on %s, from API call:\n    ' % today +\
               'https://api.census.gov/data/2014/pep/cochar5?get = AGEGRP, ' +\
               'RACE5, HISP, SEX, DATE, STNAME, POP & for = county:*' +\
               ' & in = state: % s & key = MYKEY' % state
    
    apd = AreaPopDataset(df, geodf, 'FIPS', 'FIPS',
                         cat_col='ratio',
                         footnote=footnote,
                         cat_name=state + '_Female_15_to_49',
                         title=state_name + ' 2014 County Populations by Proportion of Women Ages 15 to 49',
                         percent_format=True)
    chstyle = style_dict[state]
    chmap = Choropleth(apd, chstyle, None, OUTPATH)
    choropleth_dict[state] = chmap
    chmap.plot()