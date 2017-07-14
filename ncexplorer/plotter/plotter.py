"""
The plotter module implements the base class Plotter.  mapPlotter is a subclass
specialized for maps (displaying data on a map of the surface of the Earth).
ScatterPlotter is a subclass for creating scatter plots.

@created: Mar 28, 2017
@author: neil
"""
from ncexplorer.plotter.projection import SUPPORTED_PROJECTIONS
from ncexplorer.plotter.projection import PROJECTION_DESCRIPTIONS
from ncexplorer.plotter.projection import PROJ_ORTHOGRAPHIC
from ncexplorer.plotter.projection import new_projector
from ncexplorer.const import COLOR_CONTINENTS, COLOR_COASTLINES 
from matplotlib.ticker import FixedLocator
import numpy as np
import xarray as xr


class Plotter(object):
    """The Plotter interface.
    
    There are two types of plots: scatter plots and maps.  The base class for
    scatter plots is ScatterPlotter.  The base class for maps is MapPlotter.
    
    Any Plotter class has a dataset attribute which is an xarray instance of
    a DataArray or a Dataset containing the data to be plotted.
    """
    # This implementation requires that subclasses of this class implement a
    # setter method for the dataset attribute.
    def __init__(self, **kwargs):
        
        if 'dataset' in kwargs and kwargs['dataset'] is not None:
            self.dataset = kwargs['dataset']
        
        # The subclass must set the charttype.
        self.charttype = 'None'
        self._title = None

    def set_defaults(self):
        pass

    def set_canvas(self, canvas):
        """Sets the canvas and plotting area for the plot.
        
        The canvas is the window or region in the user interface where all the
        plots are displayed.  Each individual plot is a subsection or subregion
        of this area.  In addition to setting the canvas, this method calls
        the canvas add_map method to create specific plotting area.
        """
        self._canvas = canvas

        # Schematically, the canvas is the region on which the scatter plots
        # and maps are drawn.  More concretely, it is the Matplotlib.pyplot's
        # figure instance.  The add_plot method creates a rectangle on the
        # figure for a particular plot.
        ax = self._add_plot()
        return ax

    def draw(self):
        """Render the data as contour levels on a map."""
        self._draw()
#        self._canvas.show()

    def clear(self):
        """Draws the map with continents, but no data.
        
        This method effectively clears the map."""
        # Maybe this will clear the figure.
        self._canvas.clear()
        
        self._clear()
#        self._canvas.show()
    
    def update(self):
        """Calls clear() and then draw() to update the plot."""
        self.clear()
        self.draw()

    def savefig(self, filename):
        """Save the figure to disk as a PNG file.
        
        This calls the matplotlib savefig() method.
        """
        fig = self._canvas._figure
        fig.savefig(filename)

    @property
    def projections(self):
        """Displays a list of supported projections.
        
        Map type plotters will return a list of supported projections.  Other
        types where it's not appropriate will return the short message
        explaining that the plotter type doesn't support projections.
        """
        return "Chart type {0} does not support projections.".format(
            self.charttype)

    @property
    def charttypes(self):
        return ['Skatter', 'Map']


    # The utility methods for printing the object.  These methods are useful
    # when debugging.  The debugging window in eclipse calls the __repr__ and
    # __str__ methods.
    def _pretty(self):
        # The subclass implements this.
        pass

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        pretty = self._pretty()
        return u'\n'.join(pretty)

    @property
    def dataset(self):
        """The object containing the plotted data.
        
        The object must be an xarray DataArray or Dataset, and conform to the
        following conventions:

            The object can be an xarray DataArray object, and it must have the
            appropriate dimensions defined.
            
            The object can be an xarray Dataset object with a single variable,
            and that variable must have the appropriate dimensions.
            
            The object can be an xarray Dataset object with more than one
            variable, but one of the variables must be 'var'.  That is the
            variable that is plotted.
        
        In any of these cases, object is converted to an xarray Dataset that
        conforms to the last condition.
        """
        return self._dataset

    @dataset.setter
    def dataset(self, dataobj):

        # xarray DataArrays can be plotted if they have 'lat' and 'lon'
        # dimensions
        if type(dataobj) is xr.DataArray:
            newds = dataobj.to_dataset(name='var')
            var = newds.data_vars['var']
            if self._validate_dimensions(var):
                self._dataset = newds
            
        # If the first parameter isn't an xarray DataArray, then it must be an
        # xarray Dataset.
        elif type(dataobj) is not xr.Dataset:
            msg = ("The first parameter must be a xarray DataArray or " +
                   "Dataset object.")
            raise TypeError(msg)

        # If the xarray Dataset has only one variable, presume the intention
        # is to plot that variable.
        elif len(dataobj.data_vars) == 1:
            
            # That only only one entry exists in the dictionary data_vars has 
            # been establish.  The key is unknown, but the following access in
            # this case is safe.
            var = dataobj.data_vars.values()[0]
            if self._validate_dimensions(var):
                newds = var.to_dataset(name='var')
                self._dataset = newds
            
        # The dataset has more than one variable, then it must have a avariable
        # 'var', and that is the one to be plotted.  The legitimate instance of
        # this case is when data plots are saved in Datasets.
        elif not 'var' in dataobj.data_vars:
            msg = ("The variable var not found in xarray Dataset containing "
                   "more than one variable.")
            raise TypeError(msg)

        else:
            # It is now established that dataobj is an xarray Dataset with
            # exactly one variable named 'var'.
            var = dataobj.data_vars['var']
            
            # The dataset must have a 'lat' and a 'lon' dimension.
            if self._validate_dimensions(var):
                self._dataset = dataobj
            
        return


# ScatterPloting object
class ScatterPlotter(Plotter):
    """The ScatterPlotter interface.
    
    Attributes
    ----------
        dataset: (object) An xarray DataArray or Dataset containing the data
        to be plotted.
    """
    def __init__(self, dataset=None):
        
        # The plotter subclasses should call the parent, first thing.
        Plotter.__init__(self, dataset=dataset)
        self.charttype = 'Scatter'
        
    def _add_plot(self):
        self._ax = self._canvas.add_map()
        return self._ax
#        
#        self.figure = plt.figure(figsize=(8,2))
#        self.ax = self.figure.add_axes([0.1, 0.1, 0.88, 0.88])
#        self.ax.minorticks_on()
#        pass

    # The ScatterPlotter needs the time dimension.
    def _validate_dimensions(self, var):
        if not ('time' in var.dims):
            msg = "The dimension \'time\' must be defined for a scatter plot."
            raise TypeError(msg)
        return True

    def _clear(self):
        self.ax.cla()
        
    def xticks(self, ticklist):
        xlocator = FixedLocator(ticklist)
        self._ax.xaxis.set_major_locator(xlocator)
        self._ax.set_xlim([min(ticklist), max(ticklist)])

    def yticks(self, ticklist):
        ylocator = FixedLocator(ticklist)
        self._ax.yaxis.set_major_locator(ylocator)
        self._ax.set_ylim([min(ticklist), max(ticklist)])

    def addline(self, time_, var, linetype='thick'):
        if linetype == 'thin':
            linewidth = 0.25
            color = '#bce8ce'
        else:
            linewidth = 0.50
            color = '#053619'

        retline = self._ax.plot(time_, var, '-', color=color, linewidth=linewidth)
        return retline

    def addsquare(self, x, y, **kwargs):
        self._addpoint(x, y, 's', **kwargs)

    def addcircle(self, x, y, **kwargs):
        self._addpoint(x, y, 'o', **kwargs)
        
    def _addpoint(self, x, y, shape, **kwargs):
        
        if 'color' not in kwargs:
            color='#053619'
        else:
            color = kwargs['color']

        self._ax.plot(x, y, 's', color=color, markersize=8.0)

    # Return a list of properties for the __str__ family of functions.
    def _pretty(self):
        pretty = []
        pretty.append("Type: scatter")
        return pretty
    

# The base class defines the interface.
class MapPlotter(Plotter):
    """The MapPlotter interface.
    
    Attributes
    ----------
        center: (tuple) The latitude and longitude of the center of the map.
        
        contour_colors: (list of CSS color specifications: '#rrggbb') The
        colors used for the contours.
        
        contour_levels: (list) The break points for the contour levels.
        
        dataset: (object) An xarray DataArray or Dataset containing the data
        to be plotted.
        
        projection: (string) The map projection.
    
    Methods
    -------
        emptymap(center=None): Draws an map with just the continent outlines.
        This method effectively clears the map.
        
        savefig(filespec): Saves the plot as a PNG file to the location
        specified with filespec.
    """
    def __init__(self, dataset=None):
        
        # The plotter subclasses should call the parent, first thing.
        Plotter.__init__(self, dataset=dataset)
        self.charttype = 'Map'
        
        # NOTE: The properties being set here are actually being set by the
        # setter methods defined below.
        self._projector = None
        self._showgrid = False
        
        self._color_continents = COLOR_CONTINENTS
        self._color_coastlines = COLOR_COASTLINES
        
        # The colors and contour levels are set to none, so by default, they
        # will be chosen automatically by the basemap contourf method.
        # chosen automatically.
        self._cs_levels = None
        self._cs_colors = None
        self._colorbar = True

    def set_defaults(self):
        self.projection = PROJ_ORTHOGRAPHIC

    def _add_plot(self):
        self._ax = self._canvas.add_map()
        return self._ax


    @property
    def center(self):
        """The latitude and longitude of the center of the map.
        
        A tuple (latitude, longitude) that is used by the plotting library.
        The map that is drawn is centered on this latitude and longitude.
        """
        if self._projector is None:
            msg = "Projection is undefined."
            raise TypeError(msg)
        
        return self._projector.center

    @center.setter
    def center(self, center):
        # FIX ME: Add error handling error.  Raise and exception if the center
        # specified does not conform.
        if self._projector is None:
            msg = "Projection is undefined.  Cannot set center location."
            raise TypeError(msg)
        self._projector.center = center
        self._set_basemap()

    @property
    def colorbar(self):
        return self._colorbar

    @colorbar.setter
    def colorbar(self, colorbar_on):
        self._colorbar = colorbar_on

    @property
    def contour_colors(self):
        """The user-defined contour colors.
        
        If the contour colors have not been explicitly set by the user, then
        the matplotlib library will use a default color scheme.
        """
        return self._cs_colors

    @contour_colors.setter
    def contour_colors(self, colors):
        self._cs_colors = colors

    @property
    def contour_levels(self):
        """The user-defined contour levels.
        
        If the contour levels have not been explicitly set by the user, then
        the matplotlib library will calculate contour levels from the data
        being plotted.
        """
        return self._cs_levels

    @contour_levels.setter
    def contour_levels(self, levels):
        self._cs_levels = levels

    # Subclass must validate the dataset dimensions.
    def _validate_dimensions(self, var):
        # MapPlotters require latitude and longitude.
        if not ('lat' in var.dims and 'lon' in var.dims):
            msg = ("Map plots require \'lat\' (latitude) and \'lon\' " +
                   "(longitude).")
            raise TypeError(msg)
        return True
    
    @property
    def grid(self):
        """display the lines of latitude and longitude.
        
        The lines displayed correspond to the values for latitude and
        longitude in the dataset    @property
    def charttypes(self):
        return ['']

.  The grid lines are not displayed by default.
        """
        return self._showgrid

    @grid.setter
    def grid(self, on_boolean):
        if on_boolean not in (True, False):
            msg = "The grid attribute must be True or False."
            raise TypeError(msg)
        self._showgrid = on_boolean

    @property
    def projection(self):
        """The map projection.
        
        Projections supported are:
            Lambert Azimuthal Equal Area: 'laea'
            Lambert Azimuthal Conformal: 'lcc'
            Orthographic: 'ortho'
        
        The orthographic optionally supports two projections side-by-side.  The
        right-hand map is centered on the point diametrically opposite the
        specified center.
        """
        return self._projector.projection

    @projection.setter
    def projection(self, projection):
        # If the projection is already set to what has been requested, there
        # is no need to do anything at all.
        if (self._projector is not None and
            self._projector.projection == projection):
            return

        if projection not in SUPPORTED_PROJECTIONS:
            msg = ("The specified projection \'{0}\' is not " +
                   "supported.").format(projection)
            raise TypeError(msg)
        self._projector = new_projector(projection)
        self._set_basemap()

    @property
    def projections(self):
        """Return a list of supported projections"""
        return PROJECTION_DESCRIPTIONS

    def points_to_lonlats(self, points):
        """Converts a tuplelike set of points to longitude and latitude."""
        
        # Points are defined latitude first, longitude second.
        # Points can be a single tuple.
        if type(points) is tuple:
            lats = points[0]
            lons = points[1]
            lonlats = np.meshgrid(lons, lats)
            return lonlats

        # FIX ME:  Through an exception here.
        return None

    def _pretty(self):
        pretty = []
        pretty.append("Type: map")
        pretty.append("Projection: {0}".format(self.projection))
        pretty.append("Center: {0}".format(self.center))
        return pretty
