# # Cleaning the PHC Needs Assessment Data

# This script creates county-level choropleth maps for Texas demographic data. It creates some basic classes and walks through some use cases. City and county shapefiles were created with ArcGIS. Colors were chosen using Color Brewer 2.0 (http://colorbrewer2.org/).
# <br/><br/>
# All data is publicly available. Datasets come from the U.S. Census
# Bureau; 2014 American Community Survey 5-Year Estimates
# (https://www.census.gov/programs-surveys/acs/) and the Texas State
# Demographer (http://osd.texas.gov/Data/TPEPP/Projections/).

# <b>Dependencies:</b>
# <br/>
# Python 2.7    <br/>
# pandas version 0.17.1  <br/>
# numpy version 1.10.1    <br/>
# geopandas version 0.1.0 dev 451292  <br/>
# matplotlib version 1.5.1

import datetime as dt
import numpy as np
import pandas as pd
import geopandas as gpd
import os
from choroshape import AreaPopDataset, CityInfo, Choropleth
from choroshape import fix_FIPS, get_custom_bins
from Texas_mapping_objects import Texas_city_label_df

# from IPython import get_ipython
# from IPython.core.interactiveshell import InteractiveShell

# get_ipython().magic(u'load_ext autoreload')
# get_ipython().magic(u'autoreload 2')
# get_ipython().magic(u'matplotlib inline')


# data input path
INPATH = os.path.normpath(
    'S:/FHRPD/Primary Care Needs Assessment/Data & Chart Used')

OUTPATH = os.path.normpath('S:/FHRPD/Mapping/Rachel Test')
# path for imported shapefiles
SHAPE_PATH = os.path.normpath('S:/FHRPD/Mapping/1-Templates')

# #For Testing
# OUTPATH = os.path.normpath('C:/Users/rasquith692/Desktop/Rachel Test')
# SHAPE_PATH = os.path.normpath('C:/Users/rasquith692/Desktop/Rachel Test')
# INPATH = os.path.normpath('C:/Users/rasquith692/Desktop/Rachel Test')

#For Testing on Mac
OUTPATH = os.path.expanduser('~/Desktop/Rachel Test')
SHAPE_PATH = os.path.expanduser('~/Desktop/Rachel Test')
INPATH = os.path.expanduser('~/Desktop/Rachel Test')


county_shp_filename = os.path.normpath(
    os.path.join(SHAPE_PATH, 'Counties/ArcGIS_Counties_2012.shp'))
cities_shp_filename = os.path.normpath(
    os.path.join(SHAPE_PATH, 'Cities/ArcGIS_CitiesTop_2013.shp'))


# These parameters are for annotating the footnote
today = dt.datetime.today().strftime("%m/%d/%Y")
inits = 'raa'
preparedby = 'Prepared by: Office of Program Decision Support, %s (%s)' % (
    today, inits)

# These are the columns name from the texas GeoDataFrame
geofips_col = 'FIPS'

# Column names from the city GeoDataFrame
city_geoms = 'geometry'
city_names = 'NAME'


city_info = CityInfo(cities_shp_filename, city_geoms, city_names,
                     Texas_city_label_df)


# <b>Step 2: Process the Data for the Specific Use Case</b>
# The following code takes a large csv file from the Texas State
# Demographer and creates a dataframe with categories of interest.

pop_data = pd.read_excel(os.path.normpath(os.path.join(
    INPATH,
    '1.Texas Population/TSDC_PopulationProj_County_AgeGroup Yr2014 - 1.0ms.xlsx')))


# make a df for all ages to set aside
all_data = pop_data[pop_data['age_group'] == 'ALL']


# Create a dataframe with FIPS and total women 18 to 64
rep_women = pop_data[pop_data['age_group'].isin(['18-24', '25-44', '45-64'
                                                 ])].groupby('FIPS').aggregate(
    np.sum).reset_index(level=0)
rep_women = rep_women[['FIPS', 'total_female']]
rep_women.columns = ['FIPS', 'total_women_18_to_64']

# Create a dataframe with FIPS and total population 18 and over
adults = pop_data[pop_data['age_group'].isin(['18-24', '25-44', '45-64', '65+'
                                              ])].groupby('FIPS').aggregate(
    np.sum).reset_index(level=0)

adults = adults[['FIPS', 'total']]
adults.columns = ['FIPS', 'total_18_and_over']

# Create a dataframe with FIPS and total population under 18
children = pop_data[pop_data['age_group'] == '<18']
children = children[['FIPS', 'total']]
children.columns = ['FIPS', 'under_18']

# Clean up unnecessary columns
all_data = all_data.drop(
    labels=['migration_scenario', 'year', 'age_group'], axis=1)

# Now merge the new age columns onto the others
all_data = pd.merge(all_data, rep_women, how='left', on='FIPS')
all_data = pd.merge(all_data, adults, how='left', on='FIPS')
all_data = pd.merge(all_data, children, how='left', on='FIPS')

# Get the state-level data for making bins
state_only = all_data[all_data['FIPS'] == 0]

# Now get rid of state data in the county dataset
all_data = all_data[all_data['FIPS'] != 0]


# Ratios from ACS tables have been precalculated in Excel, so less
# processing is necessary.

for_born_data = pd.read_excel(os.path.normpath(os.path.join(
    INPATH, '1.Texas Population/_Map - Foreign Born Population.xlsx')),
    skiprows=1)

poverty_data = pd.read_excel(os.path.normpath(os.path.join(
    INPATH, '2.Poverty_Unemp_Edu/_Map - Adult Poverty 200%FPL.xlsx')),
    skiprows=1)

insured_data = pd.read_excel(os.path.normpath(os.path.join(
    INPATH, '3.Health Insurance/_Map - No Health Insurance among Adults.xlsx')),
    skiprows=1)

# Get the overal state percent from the cells
state_acs = pd.concat([for_born_data.iloc[
                      :1, -1:], poverty_data.iloc[:1, -1:], insured_data.iloc[
    :1, -1:]], axis=1)
state_acs.columns = ['foreign_born', 'adults_200%FPL', 'adults_uninsured']

# Reshape
for_born_data = for_born_data.iloc[:, [0, 6]]
poverty_data = poverty_data.iloc[:, [0, 10]]
insured_data = insured_data.iloc[:, [0, 10]]

# Merge into one dataframe
acs_ratios = pd.merge(for_born_data, poverty_data, how='left', on='Id2')
acs_ratios = pd.merge(acs_ratios, insured_data, how='left', on='Id2')
acs_ratios.columns = [
    'FIPS', 'foreign_born', 'adults_200%FPL', 'adults_uninsured']

fips_col = 'FIPS'
total_col = 'total'
#Fix FIPS & set the data
data = fix_FIPS(all_data, fips_col, '48')
#specify the source text
source = 'Source: Texas State Data Center, 2014 Population Projections,\n' +\
         '            Full 2000-10 Migration Rate'
# For the demographic cats
cat_cols = ['total_anglo', 'total_black', 'total_hispanic', 'total_other',
            'total_women_18_to_64', 'total_18_and_over', 'under_18']

# Loop through the columns of interest
for c in cat_cols:
    cat_col = c
    # Assign the category name
    if c == 'total_women_18_to_64':
        cat_name = '18-64 Years of Age and Female'
    elif c == 'total_18_and_over':
        cat_name = '18 Years of Age and Older'
    elif c == 'under_18':
        cat_name = 'Younger than 18 Years of Age'
    else:
        cat_name = c[6:].title().replace('_', ' ')

    # set up cutoffs and labels
    title = 'Percent of Population who are %s by County, 2014' % cat_name
    if cat_name in ['Black', 'Other']:
        bins = [0, .9, 4.9, 9.9, 100]
    elif cat_name in ['18-64 Years of Age and Female',
                      '18 Years of Age and Older',
                      'Younger than 18 Years of Age']:
        state_level = state_only[c]/state_only[total_col]
        bins = get_custom_bins(state_level)
        # Optional label for the legend
        level_labels = {1: '(State Overall Prop.)'}
        title = 'Percent of Population %s, 2014' % cat_name
    else:
        bins = None
        level_labels = None

    # Asign non-blue clor schemes
    if cat_name == 'Black':
        colors = 'purples'
    elif cat_name == 'Hispanic':
        colors = 'oranges'
    elif cat_name == 'Anglo':
        colors = 'greens'
    else:
        colors = None
        cmap_name = None

    # Data object
    dataset = AreaPopDataset(data, county_shp_filename, fips_col,
                             geofips_col, cat_col, total_col,
                             source + '\n' + preparedby,
                             cat_name, title, bins, 4, 1, level_labels, True)

    choropleth = Choropleth(dataset, colors, city_info, OUTPATH)

    # And...make the map
    choropleth.plot()


# Total Pop
# bins = [0, 9999, 49999, 99999, 499999, 999999, 10000000]
bins = None


dataset = AreaPopDataset(data, county_shp_filename, fips_col, geofips_col,
                         None, total_col, source + '\n' + preparedby,
                         None, 'Total Population by County, 2014', bins,
                         4, 0, None, True)



#TODO these aren't working because they are already ratios
choropleth = Choropleth(dataset, 'blues', city_info, OUTPATH)

# And...make the map
choropleth.plot()


fips_col = 'FIPS'
total_col = 'total'
#Fix FIPS & set the data
data = fix_FIPS(acs_ratios, fips_col, '48')
source = 'Source: U.S. Census Bureau, American Community Survey,\n' +\
         '           2010-2014'
footnote = source + '\n' + preparedby
titles = ['Percent of Population who are Foreign Born, 2010-2014',
          'Percent of Adult Population with Income Below 200%' +
          ' of Federal Poverty Level, 2010-2014',
          'Percent of Adult Population without Health Insurance, 2010-2014']
map_colors = ['teals', 'yellows', 'reds']

for i, c in enumerate(data.columns[1:]):
    cat_col = c
    cat_name = c.title().replace('_', ' ')
    title = titles[i]
    bins = get_custom_bins(state_acs[c][0], direction='pos')
    level_labels = {0: '(State Average)'}
    colors = map_colors[i]
    total_col = None

    dataset = AreaPopDataset(data, county_shp_filename, fips_col,
                             geofips_col, cat_col, total_col,
                             source + '\n' + preparedby,
                             cat_name, title, bins, 4, 1, level_labels, True)

    choropleth = Choropleth(dataset, colors, city_info, OUTPATH)
    choropleth.ax.plot()

    # And...make the map
    choropleth.plot()
