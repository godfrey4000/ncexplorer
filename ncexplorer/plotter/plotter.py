"""
The plotter module implements the base class Plotter, the subclass MapPlotter
and the subclass ScatterPlotter.  The MapPlotter class is specialized for maps,
displaying a dataset on a projection of the surface of the Earth.
ScatterPlotter is a subclass for a time series of a dataset variable.

@created: Mar 28, 2017
@author: neil
"""
from ncexplorer.plotter.projection import SUPPORTED_PROJECTIONS
from ncexplorer.plotter.projection import PROJECTION_DESCRIPTIONS
from ncexplorer.plotter.projection import PROJ_ORTHOGRAPHIC
from ncexplorer.plotter.projection import new_projector
from ncexplorer.plotter.plotutils import extract_plot_titles
from ncexplorer.const import COLOR_CONTINENTS, COLOR_COASTLINES, LOC_UCLA
from matplotlib.ticker import FixedLocator
import numpy as np
import xarray as xr
from numpy.core.defchararray import center


class Plotter(object):
    """The Plotter interface.
    
    There are two types of plots: scatter plots and maps.  The base class for
    scatter plots is ScatterPlotter.  The base class for maps is MapPlotter.
    
    Any Plotter class has a dataset attribute which is an xarray instance of
    a DataArray or a Dataset containing the data to be plotted.
    """
    # This implementation requires that subclasses of this class implement a
    # setter method for the dataset attribute.
    def __init__(self, frame, canvas):
        
        # The subclass sets the chart type.
        self._frame = frame
        self.charttype = 'None'
        self._title = None
        self._set_charttype()
        
        # Attach to the canvas.
        self.set_canvas(canvas)

        # The initialization is quite specialized to the subclass.  This
        # mechanism ensures that all plotting objects are instantiated with
        # the same signature, and that the frame gets set.
        self._init()

    def _set_charttype(self):
        pass

    def _init(self):
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
        """Clears the plot or map.
        
        For a scatter plot, the scatter points an lines are removed.  For a
        map, the contour colors are removed, and the map is redrawn with
        just the continents."""
        self._clear()
    
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
        return ['Scatter', 'Map']

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
        
        The object must be an xarray DataArray and meet one of the following
        criteria:
        
            For the MapPlotter, which plots data onto a projection of the
            earch, latitude and longitude must be defined.
            
            For the ScatterPlotter, time must be defined.
        """
        return self._dataarray

    @dataset.setter
    def dataset(self, dataobj):
        
        # Allowing an xarray Dataset object is too complicated, since datasets
        # can have more than one variable.
        if type(dataobj) is not xr.DataArray:
            msg = ("Only Xarray DataArrays can be plotted.")
            raise TypeError(msg)

        # xarray DataArrays can be plotted only if they have 'lat' and 'lon'
        # dimensions
        if self._validate_dimensions(dataobj):
                self._dataarray = dataobj
            
        # Set the title.  The 'title' attribute is a 0-dimensional array.
        plot_titles = extract_plot_titles(self._dataarray)
        title = plot_titles['title']
        var_headline = "{0} [{1}]".format(plot_titles['name'],
                                          plot_titles['units'])
        self._title.set_text(title)
        self._ylabel.set_text(var_headline)
#        self._canvas._figure.text(0.10, 0.95, title, fontsize='large')
#        self._canvas._figure.text(0.10, 0.92, var_headline, fontsize='small')
        return


# ScatterPloting object
class ScatterPlotter(Plotter):
    """The ScatterPlotter interface.
    
    Attributes
    ----------
        dataset: (object) An xarray DataArray or Dataset containing the data
        to be plotted.
    """
    def _init(self, **kwargs):
        # Create the areas for the title and x- and y-labels.
        self._title = self._ax.set_title('')
        self._ylabel = self._ax.set_ylabel('')
        self._xlabel = self._ax.set_xlabel('')

    def _set_charttype(self):
        self.charttype = 'Scatter'
        
    def _add_plot(self):
        self._ax = self._canvas.add_map()
        return self._ax

    # The ScatterPlotter needs the time dimension.
    def _validate_dimensions(self, var):
        if not ('time' in var.dims):
            msg = "The dimension \'time\' must be defined for a scatter plot."
            raise TypeError(msg)
        return True

    def _clear(self):
        pass
#        self._ax.cla()

    def _set_title(self, var):
        plot_titles = extract_plot_titles(var)
        title = plot_titles['title']
        self._title.set_text(title)
        
    def _set_ytitle(self, var):
        plot_titles = extract_plot_titles(var)
        var_headline = "{0} [{1}]".format(plot_titles['name'],
                                          plot_titles['units'])
        self._ylabel.set_text(var_headline)

    def _set_xtitle(self, var):
        plot_titles = extract_plot_titles(var)
        var_headline = "{0} [{1}]".format(plot_titles['name'],
                                          plot_titles['units'])
        self._xlabel.set_text(var_headline)

    def plot(self, x, y, **kwargs):
        # check that x and y are data arrays.
        
        # Sometimes, writing a plot title and axes titles is not wanted.
        write_titles = True
        if 'titles' in kwargs:
            write_titles = kwargs['titles']
            
        if write_titles:    
            self._set_title(y)
            self._set_ytitle(y)
            self._set_xtitle(x)

        self._addline(x, y, **kwargs)
        
    def xticks(self, ticklist):
        xlocator = FixedLocator(ticklist)
        self._ax.xaxis.set_major_locator(xlocator)
        self._ax.set_xlim([min(ticklist), max(ticklist)])

    def yticks(self, ticklist):
        ylocator = FixedLocator(ticklist)
        self._ax.yaxis.set_major_locator(ylocator)
        self._ax.set_ylim([min(ticklist), max(ticklist)])

    def _addline(self, x, y, **kwargs):
        if 'linetype' in kwargs:
            linetype = kwargs['linetype']
        else:
            linetype = 'thick'

        if linetype == 'thin':
            linewidth = 0.25
            color = '#bce8ce'
        else:
            linewidth = 0.50
            color = '#053619'

        retline = self._ax.plot(x.values, y.values, '-', color=color, linewidth=linewidth)
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
        The orthographic projection ('ortho') will render the displayed map
        with this position in the center.
        
        continent: (dictionary) The Lambert conformal projection displays
        entire continents, which are selected with this attribute.  The
        dictionary contains the standard latitudes, central latitude and
        longitude, and the vertical and horizontal extents in meters.

        Predefined continents are defined in ncexplorer.const:
            LAMBERT_NORTH_AMERICA
            LAMBERT_SOUTH_AMERICA
            LAMBERT_EUROPE
            LAMBERT_ASIA
            LAMBERT_AFRICA
            LAMBERT_AUSTRALIA
            LAMBERT_ANTARTICA

        corners: (list of tuples) The lower left and upper right corners of a
        map.  This attribute applies only to projections that render latitudes
        and longitudes as horizontal and vertical lines.
        
        colorbar: (True or False)  When set to True, a legend is displayed
        to the right of the map indicating the range of values corresponding
        to the colors.  The default is True.

        contour_colors: (list of CSS color specifications: '#rrggbb') The
        colors used for the contours.
        
        contour_levels: (list) The break points for the contour levels.
        
        dataset: (object) An xarray DataArray or Dataset containing the data
        to be plotted.        to_coords = Grid(73, 144)


        grid: (True or False) When set to True, the latitudes and longitudes
        defined in the dataset are rendered as lines on the plot.  When set to
        False, these values are not displayed.  The default is False.
        
        projection: (string) The map projection.  A list of the supported
        projections can be displayed with the projections attribute.
        
        projections: (list) The list of supported projections
    
    Methods
    -------
        savefig(filespec): Saves the plot as a PNG file to the location
        specified with filespec.
    """
    def _set_charttype(self):
        self.charttype = 'Map'

    def _init(self, **kwargs):
        
        self._color_continents = COLOR_CONTINENTS
        self._color_coastlines = COLOR_COASTLINES
        
        # Inherit all the default plotting parameters from the frame.
        self._projector = None
        if self._frame._projection is not None:
            self.projection = self._frame._projection
        else:
            self.projection = PROJ_ORTHOGRAPHIC

        self.center = self._frame._center
        self.continent = self._frame._continent
        self.corners = self._frame._corners
        self.contour_levels = self._frame._contour_levels 

        # Defaults.
        self._showgrid = False
        self._cs_colors = None
        
        # This is a boolean that determines if the colorbar ledged should be
        # displayed on the plot.
        self._colorbar = None
        
        # This is a variable holding the colorbar object.
        self._cb = None
        
        # Title area.
        self._title = self._canvas._figure.text(0.10, 0.95, '', fontsize='large')
        self._ylabel = self._canvas._figure.text(0.10, 0.92, '', fontsize='small')
        
        
    def _add_plot(self):
        self._ax = self._canvas.add_map()
        return self._ax

    # Many of the properties depend on a projector being set.  If it has not
    # been set, this method is called to raise and error.
    def _no_projector_exception(self):
        raise TypeError("The projection has not been defined.")

    @property
    def center(self):
        """The latitude and longitude of the center of the map.
        
        A tuple (latitude, longitude) that is used by the plotting library.
        The map that is drawn is centered on this latitude and longitude.
        """
        if self._projector is None:
            self._no_projector_exception()
        
        return self._projector.center

    @center.setter
    def center(self, center):
        if center is None:
            return

        # FIX ME: Add error handling.  Raise an exception if the center
        # specified does not conform.
        if self._projector is None:
            self._no_projector_exception()
        self._projector.center = center
        self._set_basemap()

    @property
    def continent(self):
        """The continent for a Lambert conformal conic projection..
        
        The Lambert conformal projection is best suited for entire continents.
        The continent is therefore a dictionary describing the standard
        latitudes, central longitude and latitude and the height and width of
        the region..
        """
        if self._projector is None:
            self._no_projector_exception()
        
        return self._projector.continent

    @continent.setter
    def continent(self, continent):
        if continent is None:
            return

        if self._projector is None:
            self._no_projector_exception()
        self._projector.continent = continent
        self._set_basemap()

    @property
    def corners(self):
        """The lower left and upper right corners of a rectangular projection.
        """
        if self._projector is None:
            self._no_projector_exception()
        return self._projector.corners

    @corners.setter
    def corners(self, corners):
        if corners is None:
            return

        if self._projector is None:
            self._no_projector_exception()
        self._projector.corners = corners
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
    def charttypes(self):
        return ['']

    @property
    def grid(self):
        """display the lines of latitude and longitude.
        
        The lines displayed correspond to the values for latitude and
        longitude in the dataset.  The grid lines are not displayed by default.
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
