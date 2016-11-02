'''This script imports birth file data and makes maps for the Texas Healthy Babies Databook'''

import choroshape as cshp
import datetime as dt
import numpy as np
import pandas as pd
import geopandas as gpd
import sys
import os
from six.moves import input
from Texas_mapping_objects import Texas_city_label_df

FPATH = os.path.normpath('S:/FHRPD/Healthy Texas Babies/Data & Figures/Healthy Texas Babies Data Book/2016/')
INFILE = os.path.normpath(os.path.join(FPATH, 'HTBmapdata.csv'))
df = pd.read_csv(INFILE)

df = df[df['year'] == 2014]

pivoted = df.pivot('FIPS', 'type')

print(pivoted)


