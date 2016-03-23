from lxml import etree
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib
from matplotlib.colors import Normalize
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
from pysal.esda.mapclassify import Natural_Breaks as nb
from descartes import PolygonPatch
import fiona
from itertools import chain

# Convenience functions for working with colour ramps and bars
def colorbar_index(ncolors, cmap, labels=None, **kwargs):
    """
    This is a convenience function to stop you making off-by-one errors
    Takes a standard colour ramp, and discretizes it,
    then draws a colour bar with correctly aligned labels
    """
    cmap = cmap_discretize(cmap, ncolors)
    mappable = cm.ScalarMappable(cmap=cmap)
    mappable.set_array([])
    mappable.set_clim(-0.5, ncolors+0.5)
    colorbar = plt.colorbar(mappable, **kwargs)
    colorbar.set_ticks(np.linspace(0, ncolors, ncolors))
    colorbar.set_ticklabels(range(ncolors))
    if labels:
        colorbar.set_ticklabels(labels)
    return colorbar

def cmap_discretize(cmap, N):
    """
    Return a discrete colormap from the continuous colormap cmap.

        cmap: colormap instance, eg. cm.jet. 
        N: number of colors.

    Example
        x = resize(arange(100), (5,100))
        djet = cmap_discretize(cm.jet, 5)
        imshow(x, cmap=djet)

    """
    if type(cmap) == str:
        cmap = get_cmap(cmap)
    colors_i = np.concatenate((np.linspace(0, 1., N), (0., 0., 0., 0.)))
    colors_rgba = cmap(colors_i)
    indices = np.linspace(0, 1., N + 1)
    cdict = {}
    for ki, key in enumerate(('red', 'green', 'blue')):
        cdict[key] = [(indices[i], colors_rgba[i - 1, ki], colors_rgba[i, ki]) for i in xrange(N + 1)]
    return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d" % N, cdict, 1024)

def get_data_from_bounds(bds):
    ll = (bds[0], bds[1])
    ur = (bds[2], bds[3])
    coords = list(chain(ll, ur))
    w, h = coords[2] - coords[0], coords[3] - coords[1]
    return {'coords' : coords, 'w' : w, 'h' : h}

shp = fiona.open('data/london_wards.shp')
bds = shp.bounds
shp.close()

bounds_dictionary = get_data_from_bounds(bds)

extra = 0.05

m = Basemap(
    projection='tmerc',
    lon_0=-2.,
#    lon_0=-0.1,
    lat_0=49.,
#    lat_0=51.51,
    ellps = 'WGS84',
    llcrnrlon=bounds_dictionary['coords'][0] + extra * bounds_dictionary['w'],
    llcrnrlat=bounds_dictionary['coords'][1] + extra + 0.01 * bounds_dictionary['h'],
    urcrnrlon=bounds_dictionary['coords'][2] - extra * bounds_dictionary['w'],
    urcrnrlat=bounds_dictionary['coords'][3] - extra + 0.01 * bounds_dictionary['h'],
#    llcrnrlon=-7.15,
#    llcrnrlat=50.49,
#    urcrnrlon=2.06,
#    urcrnrlat=52.54,
    lat_ts=0,
    resolution='i',
    suppress_ticks=True)
m.readshapefile(
    'uk_postcodes/Distribution/Sectors',
    'london',
    color='none',
    zorder=2)

df_map = pd.DataFrame({'poly': [Polygon(xy) for xy in m.london], 'postcode': [ward['name'] for ward in m.london_info]})
df_map['area_m'] = df_map['poly'].map(lambda x: x.area)
df_map['area_km'] = df_map['area_m'] / 100000

## Get area of parking spaces in district
interesting_postcodes = pd.read_csv('interestingpostcodes.csv')
valuations_data = pd.read_csv('valuationData.csv')

valuations_data['Postcode'] = valuations_data.Address.apply(lambda x: x.split(',')[-1].strip())

postcode_frame = interesting_postcodes

useful_valuations = valuations_data.merge(postcode_frame, how='inner', on=['Postcode'])
useful_valuations['Area'] = useful_valuations.Area.fillna(0)
useful_valuations['PostcodeBit'] = useful_valuations.Postcode.apply(lambda x: x.split()[0] + ' ' + x.split()[1][0])

area_per_district = useful_valuations.groupby('PostcodeBit').sum().Area.reset_index()
area_per_district.columns = ['postcode', 'area_of_parking']

df_map = df_map.merge(area_per_district, how='left', on=['postcode'])
df_map['area_parking_km'] = df_map.area_of_parking / 100000.
df_map['density_km'] = df_map.area_parking_km / df_map.area_km

## Refresh bounds
bounds_dataframe = pd.DataFrame([entry.bounds for entry in df_map.poly.values])
bounds_dataframe.columns = ['MinX', 'MinY', 'MaxX', 'MaxY']
min_x = bounds_dataframe['MinX'].min()
min_y = bounds_dataframe['MinY'].min()
max_x = bounds_dataframe['MaxX'].max()
max_y = bounds_dataframe['MaxY'].max()

lower_point = m(min_x, min_y, inverse=True)
upper_point = m(max_x, max_y, inverse=True)

llcrnrlon = lower_point[0]
llcrnrlat = lower_point[1]
urcrnrlon = upper_point[0]
urcrnrlat = upper_point[1]

breaks = nb(
        df_map[df_map['density_km'].notnull()].density_km.values,
        initial=300,
        k=6)

jb = pd.DataFrame({'jenks_bins': breaks.yb}, index=df_map[df_map['density_km'].notnull()].index)
df_map = df_map.join(jb)
df_map.jenks_bins.fillna(-1, inplace=True)

jenks_labels = ["<= %.3f/km$^2$(%s districts)" % (b, c) for b, c in zip(breaks.bins, breaks.counts)]
jenks_labels.insert(0, 'Parking density (%s districts)' % len(df_map[df_map['density_km'].isnull()]))

plt.clf()
fig = plt.figure()
ax = fig.add_subplot(111, axisbg='w', frame_on=False)

# use a blue colour ramp - we'll be converting it to a map using cmap()
cmap = plt.get_cmap('Blues')
# draw wards with grey outlines
df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, ec='#555555', lw=.2, alpha=1., zorder=4))
pc = PatchCollection(df_map['patches'], match_original=True)
# impose our colour map onto the patch collection
norm = Normalize()
color_map = cmap(norm(df_map['jenks_bins'].values))
to_modify = pd.DataFrame(color_map)
to_modify.ix[df_map[df_map.postcode == 'EC1V 1'].index] = np.array([[1,1,0,1],[1,1,0,1],[1,1,0,1]])
pc.set_facecolor(np.array(to_modify))
ax.add_collection(pc)

# Add a colour bar
cb = colorbar_index(ncolors=len(jenks_labels), cmap=cmap, shrink=0.5, labels=jenks_labels)
cb.ax.tick_params(labelsize=6)

# Draw a map scale
m.drawmapscale(
    bounds_dictionary['coords'][0] + 0.08, bounds_dictionary['coords'][1] + 0.015,
    bounds_dictionary['coords'][0], bounds_dictionary['coords'][1],
    10.,
    barstyle='fancy', labelstyle='simple',
    fillcolor1='w', fillcolor2='#555555',
    fontcolor='#555555',
    zorder=5)
# this will set the image width to 722px at 100dpi
plt.tight_layout()
fig.set_size_inches(7.22, 5.25)
plt.savefig('london_parking.png', dpi=500, alpha=True)
plt.show()
