'''
Created on Dec 27, 2016

@author: neil
'''
import code
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt


def plotdata(var):
    lat_0 = 33.6
    lon_0 = -117.9
    map = Basemap(projection='ortho', lat_0=lat_0, lon_0=lon_0)
    map.drawcoastlines(linewidth=0.5, color='#666666')
    map.fillcontinents(color='#cccccc', alpha=0.5)
    
    # FIX ME:  These lvels are hard coded.  This is a workaround to the
    # current problem of using 1e+20 to represent missing values.  The
    # contourf method treats this as a data value.  So the resulting plot is
    # all red over the continents and all blue over the oceans, since there is
    # really on two values: 1e+20 and anything else.
#    levels = [225, 235, 245, 255, 265, 275, 285, 295, 305, 315, 325]
    levels = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
    
    lat = var['lat']
    lon = var['lon']
    lons, lats = np.meshgrid(lon, lat)
    x, y = map(lons, lats)
    
    code.interact(local=locals())
    
    cs = map.contourf(x, y, var, levels=levels)
    cbar = map.colorbar(cs)
    plt.show()
