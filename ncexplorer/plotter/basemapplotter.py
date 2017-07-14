"""
Created on Mar 28, 2017

@author: neil

These plotters use the TkAGG interactive backend.  They are intended for a
console application or the desktop.
"""
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import addcyclic
import numpy as np
#import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from ncexplorer.plotter.plotter import MapPlotter
# from pygments.lexers.basic import BlitzMaxLexer

        
# This class servers the console app.
class BasemapPlotter(MapPlotter):
    
#    def __init__(self, **kwargs):
#
#        MapPlotter.__init__(self, **kwargs)

    # this method requires that the pyplot axes has been already created.
    def _set_basemap(self):
        self._map = self._projector.set_basemap(self._ax)

    def clear(self):
        
        self._ax.cla()
        self._map.drawmapboundary()
        self._map.drawcoastlines(linewidth=0.5, color=self._color_coastlines)
        self._map.fillcontinents(color=self._color_continents, alpha=0.5)

    # Plot a point.
    def plotpoints(self, points, color=None, pointsize=None):
        
        lonlats = self.points_to_lonlats(points)
        if color is None:
            color = '#0000FF'
        if pointsize is None:
            pointsize = 4
        
        x, y = self._projector._map(lonlats[0], lonlats[1])
        self._map.plot(x, y, 'o', color=color, markersize=pointsize)

    def _draw(self, **kwargs):
        
        # It's possible to call draw() without the dataset being set as an
        # attribute of the parent class.  so handle that case with an
        # informative error.
        try:
            var = self.dataset.data_vars['var']
        except AttributeError:
            msg = "Has the dataset been set?"
            raise AttributeError(msg)

        # TODO: The (x,y)-coordinate grid does not need to be recalculated
        # every time.  Check for compatibility, and recalculate only when
        # necessary.
        lat = var['lat']
        lon = var['lon']
        
        # Make the data wrap around the globe, instead of leaving a slice of
        # empty space between the last longitude and the first.
        #
        # Sometimes this works, sometimes it fails to broadcast the input
        # array.  In this case, we'll take the plot with a slice missing.
        try:
            data, cyclic_lon = addcyclic(var, lon)
        except ValueError:
            data = var
            cyclic_lon = lon
        
        lons, lats = np.meshgrid(cyclic_lon, lat)
        xl, yl = self._map(lons, lats)
        cs = self._map.contourf(xl, yl, data, levels=self.contour_levels, colors=self.contour_colors)#, alpha=0.5)

        # The _showgrid attribute means that the grid (lat, lon) should be
        # displayed on the map.
        if self._showgrid:
            self._map.drawparallels(lat.values)
            self._map.drawmeridians(lon.values)

        # FIXME: Once the reason for this causing an error in jupyter notebooks
        # is discovered, this test can be removed.
        if self._colorbar and self._canvas.colorbar_ok():
            self._map.colorbar(cs)


# This class serves the Tk desktop GUI application.
class TkPlotter(BasemapPlotter):
    
    # Only the __init__ method needs to be implemented.  The Tk frame manages
    # the canvas on which the map is drawn.  The remaining methods are
    # indifferent to how the canvas is managed.
    def __init__(self, dpi, width, height, center=None):
        """Sets the Tk canvas as the figure and axes."""

        self.figure = Figure(dpi=dpi, figsize=(width,height))
        self.axes = self.figure.add_subplot(111)
        
        # Need the parent to initialize.
        BasemapPlotter.__init__(self, center)

    # This is the call that's specific to this class.
    def _set_basemap(self):
        self._map = Basemap(ax=self.axes,
                            projection='ortho',
                            lat_0=self._center[0],
                            lon_0=self._center[1])
