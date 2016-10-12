## Synopsis

ChoroShape is a software package designed to help data analysts without GIS expertise efficiently and cheaply create choropleth maps for presenting county-level data. ChoroShape is an open-source tool built on existing Python libraries—primarily GeoPandas, Pandas, numpy, and matplotlib. ChoroShape uses user-defined shapefiles or geopandas.data structures and user-defined county-level dataset. 
* To avoid requiring specialized GIS knowledge, the tool utilizes user-specified map shapefiles.
* A single entry point (“make_choropleth”) allows for simple, one-line map creation.
* The AreaPopDataset object accommodates ratio, percent, or count data and can split data by quantiles or user-specified cutoffs.
* The ChoroplethSyle object allows users to easily manipulate design elements.
* The CityInfo and CityLabel objects permit users to overlay cities 


## Code Example

```
    dataset = AreaPopDataset(data, county_shp_filename, fips_col,
                             geofips_col, c, None,
                             footnote,
                             cat_name, title, bins, 4, 1, level_labels, True)

    choropleth = Choropleth(dataset, colors, city_info, OUTPATH)
    choropleth.plot()
```

## Motivation

Choroshape aims to help analysts automate choropleth map creation.

## Installation

Instillation is from github at https://github.com/rasquith/choroshape.git.


## Tests

Software is in alpha and tests are currently under development

## Contributors

Choroshape was originally designed by R.A. Asquith at https://github.com/rasquith while working the Texas Department of State Health Services. Contributions can be made through github at https://github.com/rasquith/choroshape.

## License

MIT
