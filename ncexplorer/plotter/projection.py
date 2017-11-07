"""
ncexplorer.plotter.projection
-----------------------------

This module contains wrapper classes for some of the large set of projections
implemented in Matplotlib.pyplot.

@created: May 30, 2017
@author: neil
"""
from ncexplorer.const import LOC_UCLA as UCLA
from ncexplorer.const import LAMBERT_NORTH_AMERICA
from mpl_toolkits.basemap import Basemap


# Equidistant Cylindrical Projection.
# From Basemap Matplotlib Toolkit documentation: The simplest projection, just
# displays the world in latitude/longitude coordinates.
PROJ_EQUIDISTANT_CYLINDRICAL = 'cyl'

# Mercator
# From Basemap Matplotlib Toolkit documentation: A cylindrical, conformal
# projection. Very large distortion at high latitudes, cannot fully reach the
# polar regions.
PROJ_MERCATOR = 'merc'

# Lambert Azimuthal Equal Area.
# From Basemap Matplotlib Toolkit documentation: An equal-area projection. The
# green shapes drawn on the map are equal-area circles on the surface of the
# earth. Known as Tissot's indicatrix, they can be used to show the angular
# and areal distortion of a map projection. On a conformal projection, the
# shape of the circles is preserved, but the area is not. On a equal-area
# projection, the area is preserved but the shape is not.
PROJ_LAMBERT_AZIMUTHAL_EQUAL_AREA = 'laea'

# Lambert Conformal Projection.
# From Basemap Matplotlib Toolkit documentation: A conformal projection. The
# green shapes drawn on the map are equal-area circles on the surface of the
# earth. Known as Tissot's indicatrix, they can be used to show the angular
# and areal distortion of a map projection. On a conformal projection, the
# shape of the circles is preserved, but the area is not. On a equal-area
# projection, the area is preserved but the shape is not.
PROJ_LAMBERT_CONFORMAL = 'lcc'

# Orthographic Projection
# From Basemap Matplotlib Toolkit documentation: The orthographic projection
# displays the earth as a satellite (in an orbit infinitely high above the
# earth) would see it.
PROJ_ORTHOGRAPHIC = 'ortho'

# Double Orthographic Projection
# This is two orthographic projections side by side.  The left is as described
# above.  The right differs from the left in that the center of the right is
# the polar opposite point of the center of the left.
PROJ_ORTHOGRAPHIC_2 = 'ortho2'

SUPPORTED_PROJECTIONS = [PROJ_EQUIDISTANT_CYLINDRICAL,
                         PROJ_MERCATOR,
                         PROJ_ORTHOGRAPHIC,
                         PROJ_ORTHOGRAPHIC_2,
                         PROJ_LAMBERT_CONFORMAL,
                         PROJ_LAMBERT_AZIMUTHAL_EQUAL_AREA]

PROJECTION_DESCRIPTIONS = [
    {'projection': PROJ_EQUIDISTANT_CYLINDRICAL,
     'description': 'Equidistant Cylindrical'},
    {'projection': PROJ_MERCATOR, 'description': 'Mercator'},
    {'projection': PROJ_ORTHOGRAPHIC, 'description': "Orthoographic"},
    {'projection': PROJ_ORTHOGRAPHIC_2, 'description': "Double Orthoographic"},
    {'projection': PROJ_LAMBERT_CONFORMAL, 'description': "Lambert Conformal"},
    {'projection': PROJ_LAMBERT_AZIMUTHAL_EQUAL_AREA,
     'description': "Lambert Azimuthal Equal Area"}]


# Utility function to create a new class.  This function eliminates the need
# for other modules to have knowledge of class names.
def new_projector(projection):
    """Utility function for creating new instances of a projection class."""
    if projection == PROJ_EQUIDISTANT_CYLINDRICAL:
        return ProjEquidistantCylindrical()

    elif projection == PROJ_MERCATOR:
        return ProjMercator()

    elif projection == PROJ_ORTHOGRAPHIC:
        return ProjOrthographic()

#    elif projection == PROJ_ORTHOGRAPHIC_2:
#        return ProjOrthographic2()
    elif projection == PROJ_LAMBERT_CONFORMAL:
        return ProjLambertConformal()

    elif projection == PROJ_LAMBERT_AZIMUTHAL_EQUAL_AREA:
        return ProjLambertAzimuthal()


# Projection classes.
class Projector(object):
    """Base class for projections.
    
    The projection classes manage the canvas sizes and basemap initialization
    routines.
    """
    def __init__(self, projection):
        self.projection = projection
        self.projections = SUPPORTED_PROJECTIONS
    
    def __str__(self):
        return PROJECTION_DESCRIPTIONS[self.projection]
    
    # The method set_basemap is specific to the subclass and must be
    # implemented there.
    def set_basemap(self, ax):
        """Sets the projection and the region for the map."""
        self._map = self._set_basemap(ax)
        return self._map


class ProjOrthographic(Projector):
    """A Projector class for an orthographic projection.
    
    The orthographic projection requires a center.  The campus of UCLA is the
    default center.
    """
    def __init__(self, center=None):
        Projector.__init__(self, PROJ_ORTHOGRAPHIC)
        
        if center is None:
            self.center = UCLA
        else:
            self.center = center

    def _set_basemap(self, ax):
        mapobj = Basemap(ax=ax,
                      projection=self.projection,
                      lat_0=self.center[0],
                      lon_0=self.center[1])
        return mapobj


# This class
class ProjLambertConformal(Projector):
    """A Projector class for the Lambert conformal projection.
    
    This projection is best suited for continents.  North America is the
    default.
    """
    def __init__(self):
        Projector.__init__(self, PROJ_LAMBERT_CONFORMAL)

        # Difficult to specify the parameter for a Lambert conformal
        # projection.  So instead, just support specifying continents.
        # North America is the default.
        self.continent = LAMBERT_NORTH_AMERICA
        self._calculate_params()

    # Setup the parameters.
    def _calculate_params(self):
        self.params = {
            'width': self.continent['width'],
            'height': self.continent['height'],
            'rsphere': (6378137.00, 6356752.3142),
            'resolution': 'l',
            'area_thresh': 1000.0,
            'lat_1': self.continent['standard_lat_S'],
            'lat_2': self.continent['standard_lat_N'],
            'lat_0': self.continent['center_lat'],
            'lon_0': self.continent['center_lon']
        }
 
    def _set_basemap(self, ax):
        self._calculate_params()
        mapobj = Basemap(ax=ax,
                         projection=self.projection,
                         width=self.params['width'],
                         height=self.params['height'],
                         rsphere=self.params['rsphere'],
                         resolution=self.params['resolution'],
                         area_thresh=self.params['area_thresh'],
                         lat_1=self.params['lat_1'],
                         lat_2=self.params['lat_2'],
                         lat_0=self.params['lat_0'],
                         lon_0=self.params['lon_0'])
        return mapobj


class ProjLambertAzimuthal(Projector):
    """A Projector class for the Lamber azimuthal projection."""
    def __init__(self):
        Projector.__init__(self, PROJ_LAMBERT_AZIMUTHAL_EQUAL_AREA)

        # FIXME: Calculate these parameters from a simpler request such as a
        # center and a size.
        self.params = {
            'width': 12000000,
            'height': 8000000,
            'resolution': 'l',
            'lat_ts': 50.0,
            'lat_0': 50.0,
            'lon_0': -107.0}

    def _set_basemap(self, ax):
        mapobj = Basemap(ax=ax,
                         projection=self.projection,
                         width=self.params['width'],
                         height=self.params['height'],
                         resolution=self.params['resolution'],
                         lat_1=self.params['lat_ts'],
                         lat_0=self.params['lat_0'],
                         lon_0=self.params['lon_0'])
        return mapobj


# This class is the parent class for map projects that fit into a rectangle.
# The defining property is the lower-left corner and the upper-right corner.
class ProjectorFlat(Projector):
    
    def __init__(self, projection):
        Projector.__init__(self, projection)
        
        # The internal corners property is a dicationaary.
        self._corners = {}

        # FIXME: It would be nice to go from 180 to 180, but that either
        # produces a div/0 exception, or (-180, 180) paints only half the map.
#        self.corners = {
#            'llcrnrlat': -90.0,
#            'llcrnrlon': 0,
#            'urcrnrlat': 90.0,
#            'urcrnrlon': 360}
        self.corners = [(-85,0), (85,360)]

    @property
    def corners(self):
        ret = [
            (self._corners['llcrnrlat'], self._corners['llcrnrlon']),
            (self._corners['urcrnrlat'], self._corners['urcrnrlon'])]
        return ret

    @corners.setter
    def corners(self, corners):
        self._corners['llcrnrlat'] = corners[0][0]
        self._corners['llcrnrlon'] = corners[0][1]
        self._corners['urcrnrlat'] = corners[1][0]
        self._corners['urcrnrlon'] = corners[1][1]

    def _set_basemap(self, ax):
        mapobj = Basemap(ax=ax,
                      projection=self.projection,
                      llcrnrlat=self._corners['llcrnrlat'],
                      llcrnrlon=self._corners['llcrnrlon'],
                      urcrnrlat=self._corners['urcrnrlat'],
                      urcrnrlon=self._corners['urcrnrlon'])
        return mapobj


class ProjEquidistantCylindrical(ProjectorFlat):
    """A Projector class for the equidistant cylindrical projection.
    
    The boundaries of this projection start at -90 deg latitude to +90 deg
    latitude, and 0 deg longitude to 360 deg longitude.
    """
    def __init__(self):
        ProjectorFlat.__init__(self, PROJ_EQUIDISTANT_CYLINDRICAL)

        
class ProjMercator(ProjectorFlat):
    """A Projector class for the Mercator projection.
    
    The boundaries of this projection are -80 deg latitude to +80 deg
    latitude and 0 deg longitude to 360 deg longitude.
    """
    def __init__(self):
        ProjectorFlat.__init__(self, PROJ_MERCATOR)
        self.corners = [(-80.0, 0), (80.0, 360)]
