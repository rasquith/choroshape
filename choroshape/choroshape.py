# TODO make it handle missing data

from __future__ import unicode_literals

__all__ = [
    'clean_FIPS',
    'fix_FIPS',
    'get_custom_bins',
    'make_choropleth',
    'AreaPopDataset',
    'CityInfo',
    'CityLabel',
    'ChoroplethStyle',
    'Choropleth'
]

# Patch for basestring
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib
import os
import textwrap
import re
import math

from matplotlib import pyplot as plt, patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, hex2color


def clean_FIPS(FIPS_code):
    '''Converts a number sequence to a string and removes alphanumeric
    characters.'''
    FIPS_code = str(FIPS_code)
    FIPS_code = re.sub('[\W_]+', '', FIPS_code)
    if re.match('^[0-9]*$', FIPS_code) is None:
        raise ValueError('Data contains non-digit FIPS code values')
    return FIPS_code


def fix_FIPS(data, county_col, state_FIPS=None):
    '''Takes FIPS data and outputs a dataframe with a FIPS column containing
    5-digit, merged, state and county FIPS codes.
    Args:
        data(pandas DataFrame): data with FIPS columns
        county_col(str): name of column with county FIPS codes.
        state_FIPS(str): either the name of the column with state FIPS codes
            or a 2-digit state FIPS code in string format, e.g. ('25)
            can be none if county_col has combiend, 5-digit codes
    Returns:
        data(pandas DataFrame): with combined FIPS column added'''

    FIPS_col = 'FIPS'  # name of the FIPS column to be added

    # Check for null values
    if data[county_col].isnull().values.any():
        raise ValueError('Data contains empty FIPS code values.')

    # Clean the county codes
    data[county_col] = data.loc[:,county_col].map(
        lambda x: clean_FIPS(x))

    data[county_col] = data.loc[:,county_col].apply(
        lambda x: x.zfill(3) if len(x) < 3 else x)

    # check if state codes need to be added
    if (data[county_col].str.len() == 3).any():
        if state_FIPS in data.columns:  # if a column name is entered
            state_col = state_FIPS
        else:
            state_FIPS = clean_FIPS(state_FIPS)
            if len(state_FIPS) != 2:
                raise ValueError('Data contains State FIPS not in a readable ' +
                                 'format. Entry must be a string column name ' +
                                 'or a 2-digit state FIPS code')
            state_col = 'state_FIPS'
            data[state_col] = state_FIPS  # create a state FIPS column

        data[state_col] = data.loc[:,state_col].map(
            lambda x: clean_FIPS(x))  # clean the state FIPS column

        data[county_col] = data.loc[:,county_col].apply(
            lambda x: x[-3:])  # Make it all consistent
        data[county_col] = data[state_col].str.cat(data[county_col], sep='')

    # Check that codes are the right length
    data[county_col] = data[county_col].str.zfill(5)  # if it drops leading zeros
    if (data[county_col].str.len() == 5).all():  # codes already combined
        data[FIPS_col] = data[county_col]
    else:
        raise ValueError(
            'Data contains FIPS code values that violate length ' +
            'requirements. Entries shold be a 3-digit county code ' +
            'or a 5-digit state and county code.')

    return data


def round_py2(x, d=0):
    '''rounds up--Python2 and Python3 have different rounding behavior'''
    p = 10 ** d
    return float(math.floor((x * p) + math.copysign(0.5, x)))/p


# TODO decide if you want this out of the object
def get_custom_bins(level, num_cats=4, dif=.1, direction=None, precision=1):
    '''Creates percent cutoff bins a certain amount away from an index
    Args:
        level(float): index marker, fractions will be multiplied by 100.
            Unless specified, the level acts as the midpoint. If the
            direction is 'pos', the level acts as the lower endpoint for the
            second lowest category_number. The level should not be zero;
            negative levels are not allowed.
        dif(float): how much the other cats should step up or down.
            This is a multiplier.
        num_cats(int): how many categories to split the bins into
        direction(str): None or pos; a positive direction makes bins from
            0 to level; otherwise level is the midpoint
        precision(int): what to round to
    Returns:
        bins(list[float]): list of bin cutoff points
        '''
    # Negative levels are not allowed
    if float(level) <= 0:
        raise ValueError(
            'Level is less than or equal to zero.' +
            'get_custom_bins only makes positive categories.')

    # Levels are assumed to be percentages
    if float(level) < 1:
        level = float(level) * 100.0
    level = round(level, 1)
    plus_mult = 1
    minus_mult = 1
    mid = int(round_py2(float(num_cats)/2))  # In case there's an odd number

    if direction == 'pos':
        bins_dict = {0: 0.0, 1: level, num_cats: 100.0}
        for i in range(2, num_cats):
            plus_mult += dif
            bins_dict[i] = round(level*plus_mult, precision)
    else:  # direction is None
        bins_dict = {0: 0.0, mid: float(level)}
        for i in range(1, mid):
            plus_mult += dif
            minus_mult -= dif
            bins_dict[mid + i] = round(level*plus_mult, 1)
            bins_dict[mid - i] = round(level*minus_mult, 1)
        bins_dict[num_cats] = 100.0

    bins = []
    for j in sorted(bins_dict, key=bins_dict.get):
        bins.append(bins_dict[j])
    return bins


def axis_data_coords_sys_transform(ax_obj_in, xin, yin, inverse=False):
    '''Goes between axis and data coordinate systems
    Args:
        axis_obj_in(matplotlib axes object): the one in use
        xin(float): x to transform
        yin(float): y to transform
        inverse(bool):
            inverse = False : Axis => Data
            True  : Data => Axis
            '''
    xlim = ax_obj_in.get_xlim()
    ylim = ax_obj_in.get_ylim()

    xdelta = xlim[1] - xlim[0]
    ydelta = ylim[1] - ylim[0]
    if not inverse:
        xout = xlim[0] + xin * xdelta
        yout = ylim[0] + yin * ydelta
    else:
        xdelta2 = xin - xlim[0]
        ydelta2 = yin - ylim[0]
        xout = xdelta2 / xdelta
        yout = ydelta2 / ydelta
    return xout, yout


def make_choropleth(data_csv, shpfile, two_digit_state_FIPS,
                    title='', footnote='', cat_name=None,
                    geoFIPS_col=None, geometry_col=None,
                    legx=.07, legy=0.18):
    '''Args:
        data_csv(str): normed path name to csv file containing data.
            1)Extension is ".csf"
            2)No lading rows or columns
            3)No footnotes, annotations, or comments
            4)Columns should be named ["FIPS",
              "category" for the population that fulfills the category
              requirment, "total" or None, any additonal columns]
            5)The data set should have at least one cateogry column or total column
        shpfile(str): normed path name to shapefile
        two_digit_state_FIPS(str or int): two digit state FIPS code,
        title(str): title for map
        footnote(str): footnote to put under the legend
        geoFIPS_col(str): name of the FIPS column in the GeoDataFrame,
            default is 'COUNTYFP'
        geometry_col(str) : name of the geometry_col, default is "geometry",
        legx(float): axis position for x of legend bounding box point
        legy(float): axis position for y of legend bounding box point
         '''
    two_digit_state_FIPS = str(two_digit_state_FIPS).zfill(2)
    data_csv = os.path.normpath(data_csv)
    shpfile = os.path.normpath(shpfile)
    data = pd.read_csv(data_csv)
    data = fix_FIPS(data, 'FIPS', two_digit_state_FIPS)
    data = data.dropna()

    geodata = gpd.GeoDataFrame.from_file(shpfile)
    if geometry_col is None:
        geometry_col = 'geometry'
    # TODO find what contains countyfp
    if geoFIPS_col is None:
        geoFIPS_col = 'COUNTYFP'
    geodata = geodata[[geoFIPS_col, geometry_col]]
    geodata.columns = ['FIPS', 'geometry']
    geodata = fix_FIPS(geodata, 'FIPS', two_digit_state_FIPS)
    geodata = (geodata[geodata['FIPS'].str.startswith(two_digit_state_FIPS)])
    geodata=geodata.dropna()

    cat_col = None
    total_col = None
    if 'category' in data.columns:
        cat_col = 'category'
    if 'total' in data.columns:
        total_col = 'total'

    apd = AreaPopDataset(data, geodata, 'FIPS', 'FIPS', cat_col,
                         total_col, footnote, cat_name, title,
                         percent_format=True)
    ch_style = ChoroplethStyle(legx=legx, legy=legy)
    chor = Choropleth(apd, ch_style)
    chor.plot()


# TODO make category for NANs
class AreaPopDataset(object):
    def __init__(self, data, geodata, FIPS_col, geoFIPS_col, cat_col=None,
                 total_col=None, footnote='', cat_name=None, title='',
                 bins=None, num_cats=4, precision=1,
                 labeled_cutoffs=None, percent_format=False):
        '''An object that holds data elements for the choropleth map.
        Attributes:
            data(pandas.DataFrame): dataframe with population data by county
                and Texas county codes or FIPS codes
            geodata(geopandas.Dataframe or str): Dataframe with shapefile
                information or the name of county shapefile with the
                extension '.shp'
            FIPS_col(str): name of the pandas df column with complete
                FIPS codes
            geoFIPS_col(str): name of the geodf column with complete
                FIPS codes
            cat_col(str): name of df column with category totals
                (e.g. 'population under 18'). If there's no category column
                specified, total population will be the assumed category of
                interest and no ratio will be calculated. Either cat_col or
                total_col or both must be specified.
            total_col(str): name of df column with total county populations.
                Either cat_col or total_col or both must be specified.
            footnote(str): Provenance info to add to the final map as
                a footnote
            cat_name(str): user determined name of population category of
                interest
            title(str): title for plot
            bins(list[floats]): cutoffs for the creation of population ratio
                groups
            num_cats(int): how many categories to have for the choropleth map
            precision(int): precision for bin cutoffs
            labeled_cutoffs(dict{category_number(int, 0-indexed),
                special label(str)}): specified labels for the categories.
                '''
        self.data = data
        # Reads in a geodtaframe or a filename and converts it
        if isinstance(geodata, gpd.GeoDataFrame):
            self.geodata = geodata
        else:
            self.geodata = gpd.GeoDataFrame.from_file(geodata)

        self.FIPS_col = FIPS_col
        self.geoFIPS_col = geoFIPS_col
        self.cat_col = cat_col
        self.total_col = total_col
        self.footnote = footnote
        self.title = title
        self.bins = bins
        self.num_cats = num_cats
        self.prec = precision
        self.punit = 10 ** (-1*self.prec)
        self.labels_col = 'labels'  # column for int
        self.labeled_cutoffs = labeled_cutoffs
        self.percent_format = percent_format
        self.grouped_col = 'group'
        # These guys will be used to map the colors and labels
        self.group_nums = []
        self.group_names = []
        self.colordict = {}

        # Set defaults for cat_name
        if cat_name is None:
            self.cat_name = 'Population'
        else:
            self.cat_name = cat_name

        # Select the valid columns for the data
        self.valid_cols = [
            x for x in [
                self.FIPS_col, self.cat_col, self.total_col] if x is not None]
        self.data = self.data.loc[:, self.valid_cols]
        self._merge_geodataframe()

        # this cycles through the valid columns to make float format
        self._totals_to_float()

        # Find which columns are being used and if needed, calculate the ratio
        self._calculate_cat()
        self._make_binned_cats()

        # Map the cutoff labels to the groups
        self._map_labels()

    def _calculate_cat(self):
        # Could have totals only
        if self.cat_col is None:
            self.calculated_cat = self.total_col
        # Or category only
        elif self.total_col is None:
            self.calculated_cat = self.cat_col
        # but if there's both it's a ratio
        else:
            self.calculated_cat = 'ratio'
            self.data[self.calculated_cat] = self.data[
                self.cat_col].astype(float)/self.data[
                self.total_col].astype(float)
        # Reformat percentages
        if self.percent_format and (self.data[self.calculated_cat] < 1).all():
            self.data[self.calculated_cat] = self.data[
                self.calculated_cat]*100.0
        # Round
        self.data[self.calculated_cat] = self.data[
            self.calculated_cat].round(self.prec)

    def _make_binned_cats(self):
        '''Makes the group column. The group column names categories according
        to the cutoff bins. Then maps the group to a column called, color,
        which codes the groups with integers''
        '''
        if self.bins is None:
            self.group_nums = range(1, self.num_cats+1)
            # qcut divides data into equal groups
            self.data['comparison'], bins = pd.qcut(self.data[self.calculated_cat],
                                     self.num_cats,
                                     labels=self.group_nums,
                                     retbins=True,
                                    precision=self.prec)
            bins = bins.round(self.prec)
            if self.prec == 0:
                bins = bins.astype(int)
            # TODO find a better fix for this
            bins = np.unique(bins)  # for too many bins/ overlaps created
            self.bins = bins.tolist()

        self.bins[0] = 0
        # TODO find a more elegant solution for this
        # punit is added to include values that have been roudnde up
        self.bins[-1] += self.punit

        self.group_nums = range(1, len(self.bins))
        self.data[self.grouped_col] = pd.cut(self.data[self.calculated_cat],
                                             self.bins, labels=self.group_nums,
                                             include_lowest=True)

    def _map_labels(self):
        '''Takes the cutoffs and creates labels)
        '''
        sign = ''
        bottom = '0'
        bottom_format = '{:1.%sf}' % str(self.prec)
        if self.percent_format:
            sign = '%'
        for i, c in enumerate(self.bins[1:]):
            cutoff = bottom_format.format(c)
            if i == 0:
                self.group_names.append(cutoff + sign + ' or less')
            elif i == len(self.bins)-2:
                self.group_names.append(bottom + sign + ' or more')
            else:
                self.group_names.append(
                    bottom + '%' + '-' + cutoff + sign)

            if self.labeled_cutoffs is not None:
                if i in self.labeled_cutoffs.keys():
                    self.group_names[i] = self.group_names[
                        i] + ' ' + self.labeled_cutoffs[i]
            bottom = bottom_format.format(c + self.punit)

        self.colordict = dict(zip(self.group_nums, self.group_names))
        self.colordict['NA'] = "insufficient data"
        # Map the label column
        self.data[self.labels_col] = self.data[
            self.grouped_col].apply(lambda x: self.colordict[x])

    def _totals_to_float(self):
        '''Makes sure population counts are float and not string
        self.data[c] could contain strings or floats
        '''
        for c in self.valid_cols[1:]:
            self.data[c] = self.data[c].apply(
                lambda x: str(x).replace(',', '')).astype(float)

    def _merge_geodataframe(self):
        '''Merges the population data with the geodataframe'''
        # merge population data with Texas GeoDataFrame
        self.data = pd.merge(left=self.geodata, right=self.data, how='left',
                             left_on=self.geoFIPS_col,
                             right_on=self.FIPS_col)


class CityInfo(object):

    def __init__(self, cities_shpfile, geometry_col, name_col,
                 label_specs_df=None):
        '''Holds city plotting information
        Attributes:
            cities_df(str): shapefile with extension .shp
            geometry_col(str): name of column with city geographies, tuples
            name_col(str): name of column with city names
            label_specs_df(pandas dataframe): dataframe with information about
                how to label cities. on the map.
                Columns MUST be arranged [city_name, positon, x-offset,
                    y-offset]. Titles okay.
            cities(numpy.series[tuples]): series of city geometry tuples
            cities_xy(list[tuples]): list of city geometry tuples
            city_names(list[str]): list of city names
            '''
        self.cities_df = gpd.GeoDataFrame.from_file(cities_shpfile)
        self.cities_df = self.cities_df[[name_col, geometry_col]]
        self.cities_df = self.cities_df.rename(
            columns={geometry_col: 'geometry', name_col: 'city_name'})
        if label_specs_df is not None:
            label_specs_df.columns = ['city_name', 'position', 'dx', 'dy']
            self.cities_df[['position', 'dx', 'dy'
                            ]] = label_specs_df[['position', 'dx', 'dy']]
        self.cities_df['coords'] = self.cities_df['geometry'].apply(
            lambda x: tuple(str(x).replace('(', '').replace(')', '').split(
                " ")[1:]))


class CityLabel(object):

    def __init__(self, city_name, coords, position='top_left',
                 dx=0.05, dy=0.05):
        '''City label object with name and label info
        Attributes:
            city_name(str): name of city
            coords(tuple(number)): city point coordinates
            position(str): where the label is oriented relative to the city
                point
            dx(float): how far away the label should be from the point on the
                x-axis
            dy(float): how far away the label should be fom the point on the
               y-axis
            text_xy(tuple): tuple of label coordinates on data axes
            '''
        self.city_name = city_name
        self.coords = coords
        self.position = position
        self.dx = dx
        self.dy = dy
        self.text_xy = ()
        self.def_position()

    def def_position(self):
        '''Determines the position of the label relative to the point in terms
        of orientation and padding
        '''
        x, y = self.coords
        if self.position == 'top_left':
            self.ha = 'right'
            self.va = 'bottom'
            text_x = float(x) - self.dx
            text_y = float(y) + self.dy
        if self.position == 'bot_left':
            self.ha = 'right'
            self.va = 'top'
            text_x = float(x) - self.dx
            text_y = float(y) - self.dy
        if self.position == 'top_right':
            self.ha = 'left'
            self.va = 'bottom'
            text_x = float(x) + self.dx
            text_y = float(y) + self.dy
        if self.position == 'bot_right':
            self.ha = 'left'
            self.va = 'top'
            text_x = float(x) + self.dx
            text_y = float(y) - self.dy
        self.text_xy = (text_x, text_y)


class ChoroplethStyle(object):

    def __init__(self, county_colors=None, border_color='#979797',
                 border_width=.6, size=None,
                 legend_loc='upper left', legx=-.01, legy=0.32,
                 ttl_align='left', ttlx=0, ttly=0.92,
                 ttl_char_limit=55):
        '''Holds style information for the choropleth plot
        Atributes:
            county_colors(str): colors name must match dict:
                (e.g. blues, greens, purples, oranges, reds)
            border_color(str): hex color for county borders and legend patch
                borders
            border_width(float): linewidth of border
            size(int) or str: resolution or dictionary key
            leg_loc(str): specifies which point of the bounding box to be used
                for positioning the legend with bbox_to_anchor
            legx(float): axis position for x of legend bounding box point
            legy(float): axis position for y of legend bounding box point
            ttl_align(str): title alignement--uses matplotlib text alignement
            ttlx(float): position of title
            ttyl(float): positino of title
            ttl_char_limit(int): this when to check to break the line
            '''
        # mMps a name onto the darkest color to use in the mapping
        self.cmap_dict = {'reds': 'darkred', 'orangereds': 'orangered',
                          'oranges': 'darkorange', 'yellows': 'darkgoldenrod',
                          'greens': 'darkgreen', 'teals': 'teal',
                          'blues': 'darkblue', 'violets': 'indigo',
                          'purples': 'darkviolet', 'texas_reds': '#B72639',
                          'texas_blues': '#2E2D71'}
        # Sets default
        if county_colors is None:
            county_colors = 'blues'
        # Color name must match a dict key
        try:
            last = self.cmap_dict[county_colors]
        except:
            raise KeyError(
                '"%s" is not a valid colormap name.' % county_colors)

        # Creates a colormap from white to darkest color
        self.cmap = LinearSegmentedColormap.from_list('my_cmap',
                                                      ['white', last])
        self.cmap_name = county_colors + '_cmap'

        # Specify the size of the image output
        img_size_dict = {'small': 75, 'med': 100, 'large': 150}
        if size is None:
            size = 'med'
        if isinstance(size, basestring):
            try:
                size = img_size_dict[size]
            except:
                raise KeyError(
                    '"%s" is not a specified size option' % size)
        self.resolution = int(size)

        # This stuff is to pass on
        self.border_color = border_color
        self.border_width = border_width

        self.legend_loc = legend_loc
        self.legx = legx
        self.legy = legy

        self.ttl_align = ttl_align
        self.ttlx = ttlx
        self.ttly = ttly
        self.ttl_char_limit = ttl_char_limit

    def get_colors(self, num_bins):
        '''Creates sequential lists of rgba colors and a
                LinearSegmentedColormap.
        All sequential color lists range from white to a dark color.
        If there are less than 6 categories, the final color is madeighter.
        Args:
            num_bins(int): number of categories to map
        Returns:
            rgbs(list[tuple[numpy.float]]]: list of rgba values

            '''
        inds = np.linspace(0, 1, num_bins)
        # if num_bins < 6:  # Colors shouldn't be so
        #     inds = inds[:num_bins-1]
        rgbs = [self.cmap(i) for i in inds]

        my_cmap = ListedColormap(
            name=self.cmap_name, colors=rgbs)
        matplotlib.cm.register_cmap(name=self.cmap_name, cmap=my_cmap)
        return rgbs


class Choropleth(object):

    def __init__(self, area_data, ch_style=None, city_info=None, out_path='',
                 savepdf=True, showplot=False):
        '''Attributes:
            area_data(AreaPopDataSet object)
            city_info(CityInfo object)
            outpath(str): path to output the plot
            ch_style(ChroplethStyle object)
            city_info(CityInfo object)
            outpath(str): specify an outpath if different than the current one
            '''
        if isinstance(ch_style, basestring) or ch_style is None:
            ch_style = ChoroplethStyle(ch_style)
        self.ch_style = ch_style
        self.area_data = area_data
        self.city_info = city_info
        self.out_path = os.path.normpath(out_path)
        self.savepdf = savepdf
        self.showplot= showplot
        self.num_bins = len(self.area_data.bins)

        self.legx = self.ch_style.legx
        self.legy = self.ch_style.legy

        self.title = self.area_data.title
        self.ttlx = self.ch_style.ttlx
        self.ttly = self.ch_style.ttly
        self.ttl_align = self.ch_style.ttl_align

        # Create the cmap for the plot
        self.rgbs = self.ch_style.get_colors(self.num_bins)

    def plot(self):
        '''Creates a county choropleth with a certain format
        '''
        self.ax = self.area_data.data.plot(column=self.area_data.grouped_col,
                                           alpha=1,
                                           cmap=self.ch_style.cmap_name,
                                           categorical=True, legend=False,
                                           linewidth=self.ch_style.border_width,
                                           edgecolor=self.ch_style.border_color)

        self.ax.set_frame_on(False)
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
        plt.tight_layout()

        if self.city_info is not None:
            self._add_cities(self.city_info.cities_df)
        self._add_title()
        self._draw_legend()
        self._add_footnote()

        if self.savepdf:
            self.save_plot()

        if self.showplot:
            self.show_plot()
        plt.close("all")

    def _add_cities(self, df):
        '''Plots and labels Texas cities'''
        cx = df['geometry'].plot(
            alpha=1, color='black', marker='o', markersize=3, ax=self.ax)
        # Now annotate the cities
        for i in df.index:

            # specify the label location
            dx = df['dx'][i]
            dy = df['dy'][i]
            position = df['position'][i]
            city_name = df['city_name'][i]
            coords = df['coords'][i]

            # transform the city coords to axis
            x, y = coords
            self.axes_point_coords = axis_data_coords_sys_transform(
                cx, float(x), float(y), True)

            # create the labels
            l = CityLabel(city_name, self.axes_point_coords, position, dx, dy)

            # transform the label coordinates back to data
            textx, texty = l.text_xy
            self.data_text_xy = axis_data_coords_sys_transform(cx, textx,
                                                               texty, False)

            # now annotate with the labels
            cx.annotate(
                l.city_name, xy=coords,
                xytext=self.data_text_xy, size='xx-small', ha=l.ha,
                va=l.va)


    def _add_title(self):
        '''Creates and positions the plot title'''
        if len(self.title) > self.ch_style.ttl_char_limit:
            self.title = "\n".join(textwrap.wrap(self.title, width=40,
                                                 break_long_words = False))
        self.ax.set_title(self.title, x=self.ttlx, y=self.ttly,
                          fontsize='large', fontname='Microsoft Sans Serif',
                          weight='semibold', ha=self.ttl_align,
                          wrap=True)

    def _draw_legend(self):
        '''Draws the legend'''
        leg_patches=[mpatches.Rectangle(xy=(0, 0),
                                          width=1, height=1, facecolor=cc,
                                          edgecolor=self.ch_style.border_color,
                                          lw=1,
                                          alpha=1
                                          ) for cc in self.rgbs]
        leg = self.ax.legend(handles=leg_patches,
                             labels=self.area_data.group_names,
                             frameon=False,
                             handleheight=1.5, handlelength=2.5,
                             fontsize='x-small', title=None,
                             bbox_to_anchor=[self.legx,
                                             self.legy],
                             loc=self.ch_style.legend_loc,
                             borderaxespad=0)

        # finding the legend extents
        fig = self.ax.figure
        fig.canvas.draw()
        renderer = fig.canvas.renderer
        leg = self.ax.get_legend()
        bb = leg.get_window_extent(renderer).transformed(
            leg.axes.transAxes.inverted())
        self.legx0 = bb.x0 + .005
        self.legx1 = bb.x1 - .005
        self.legy0 = bb.y0 - .005
        self.legy1 = bb.y1 + .005

        # Add legend title here
        self.ax.annotate('Legend',
                         color='black',
                         xy=(self.legx0, self.legy1),
                         xycoords='axes fraction',
                         ha='left', va='bottom',
                         weight='semibold',
                         size='x-small')

    def _add_footnote(self):
        '''Adds a footnote below the legend'''
        self.ax.annotate(self.area_data.footnote,
                         xy=(self.legx0, self.legy0),
                         xycoords='axes fraction',
                         va='top',
                         ha='left',
                         size=6,
                         wrap=True)

    def save_plot(self):
        '''Saves the plot to a png file and shows in the viewer'''
        # Create the output
        outfile = os.path.join(self.out_path, self.area_data.cat_name)
        plt.savefig(outfile, dpi=self.ch_style.resolution, bbox_inches='tight')
    
    def show_plot(self):
        plt.show()
