## Synopsis

ChoroShape is a software package designed to help data analysts without GIS expertise efficiently and cheaply create choropleth maps for presenting county-level data. ChoroShape is an open-source tool built on existing Python libraries—primarily GeoPandas, Pandas, numpy, and matplotlib. ChoroShape uses user-defined shapefiles or geopandas.data structures and user-defined county-level dataset. 
*To avoid requiring specialized GIS knowledge, the tool utilizes user-specified map shapefiles.
*A single entry point (“make_choropleth”) allows for simple, one-line map creation.
*The AreaPopDataset object accommodates ratio, percent, or count data and can split data by quantiles or user-specified cutoffs.
*The ChoroplethSyle object allows users to easily manipulate design elements.
*The CityInfo and CityLabel objects permit users to overlay cities 


## Code Example

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
    cat_name = c.title().replace('_', ' ')
    title = titles[i]
    bins = get_custom_bins(state_acs[c][0], direction='pos')
    level_labels = {0: '(State Average)'}
    colors = map_colors[i]

    dataset = AreaPopDataset(data, county_shp_filename, fips_col,
                             geofips_col, c, None,
                             source + '\n' + preparedby,
                             cat_name, title, bins, 4, 1, level_labels, True)

    choropleth = Choropleth(dataset, colors, city_info, OUTPATH)
    choropleth.ax.plot()

    # And...make the map
    choropleth.plot()

## Motivation

Choroshape aims to help analysts automate choropleth map creation.

## Installation

Instillation is from github at tk


## Tests

Software is in alpha and tests are currently under development

## Contributors

Choroshape was originally designed by R.A. Asquith at tk while working the Texas Department of State Health Services. Contributions can be made through github at tk.

## License

MIT
