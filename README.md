## Synopsis

Choroshape for Python creates, U.S. county-level choropleth maps for demographic datasets. Choroshape requires user to input a demographic dataset and a .shp file, such as [TIGER shapefiles](https://www.census.gov/geo/maps-data/data/tiger-line.html) from the U.S. Census site. Choroshape helps users clean demographic county-level datasets and easily create attractive, county-level choropleth maps for U.S. states

 
1. Choroshape provides methods to extract and clean demographic datasets with county FIPS codes and to calculate fields that represent the proportion of total population for specified demographic categories. 
2. The user can specify state.shp files they wish to use; allowing the user to customize map projections
3. The user can easily specify cutoffs for color bins, or let choroshape calculate optimal bin ranges
4. Choroshape style objects allow the user to easily choose single-color schemes and optimally place the legend and title on the map output. Defualt maps styles are created with matpotlib.
 See [examples](https://github.com/rasquith/choroshape/blob/master/examples/) for more details.
 
 # Example
 ![Example Choroshape Map](READMEexample.png?raw=true "Example Choroshape Map")

## Contributors

The following was originally designed by R.A. Asquith at https://github.com/rasquith while working the Texas Department of State Health Services.

## License

MIT
