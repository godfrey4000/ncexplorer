'''
Created on Dec 27, 2016

@author: neil
'''
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt

# Map defaults
UCLA = [34.07, -118.45]  # Center map on UCLA by default
COLOR_COASTLINES = '#666666'
COLOR_CONTINENTS = '#cccccc'

class Plotter(object):
    
    def __init__(self, axes=None, center=UCLA):
        self.draw(axes=axes, center=center)
        pass

    def draw(self, axes=None, center=None, time_=0, plev=0, **kwargs):
        if None == axes:
            self._map = Basemap(projection='ortho', lat_0=center[0], lon_0=center[1])
        else:
            axes.clear()
            self._map = Basemap(ax=axes, projection='ortho', lat_0=center[0], lon_0=center[1])
        self._map.drawcoastlines(linewidth=0.5, color=COLOR_COASTLINES)
        self._map.fillcontinents(color=COLOR_CONTINENTS, alpha=0.5)

        if 'var' in kwargs:
            var = kwargs['var']
            self.plotdata(var, time_, plev)
    
    def plotdata(self, var, time_=0, plev=0):
        lat = var['lat']
        lon = var['lon']
        lons, lats = np.meshgrid(lon, lat)
        x, y = self._map(lons, lats)
    
        # FIX ME: Try to be smart about the shape of the variable array.
        cs = self._map.contourf(x, y, var[time_, plev])
#        cbar = self._map.colorbar(cs)
#        plt.show()
