## Synopsis

ChoroShape is a software package designed to help public health researchers without GIS expertise efficiently and cheaply create choropleth maps for presenting county-level data. ChoroShape is an open-source tool built on existing Python libraries—primarily GeoPandas, Pandas, numpy, and matplotlib. ChoroShape uses user-defined shapefiles or geopandas.data structures and user-defined county-level dataset. ChoroShape matches geometry and category data through county FIPS codes. The package is currently being expanded to support other types of geographical areas in addition to counties.
*To avoid requiring specialized GIS knowledge, the tool utilizes user-specified map shapefiles.
*A single entry point (“make_choropleth”) allows for simple, one-line map creation.
*The AreaPopDataset object accommodates ratio, percent, or count data and can split data by quantiles or user-specified cutoffs.
*The ChoroplethSyle object allows users to easily manipulate design elements.
*The CityInfo and CityLabel objects permit users to overlay cities 
