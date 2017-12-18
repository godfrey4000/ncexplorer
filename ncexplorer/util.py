'''
Created on Dec 28, 2016

@author: neil
'''
import sys
import math
import numpy as np
import xarray as xr
from scipy.spatial import KDTree, Delaunay
from scipy.interpolate import LinearNDInterpolator
from scipy.signal import gaussian
from scipy.signal import convolve

from pydap.client import open_url
from pydap.cas.urs import setup_session


# Grid definitions
class Grid(object):
    """A latitude-longitude grid.

    Parameters
    ----------
        array (DataArray) optional: If a DataArray is passed as a parameter,
        then all other parameters are ignored.  The DataArray is presumed to
        define a latitude-longitude grid, and that is used.
        
        lat, lon (list) optional: A numpy array of the specific values for the
        latitudes and longitudes.

        name (str) optional: A short string describing the grid.  If a name is
        not passed, a default name is constructed from the cell widths.  This
        however is redundant.  For example, [-90, -60, -30, 0, 30, 60, 90] and
        [-75, -45, -15, 15, 45, 75] would both be 015x*.
    
    The python str() function will return a string nxm, where n (m) is the
    distance between lines of latitude (longitude).

    Latitudes
    ---------
    The range of latitudes is [-90, 90].  The list of latitudes may either
    include both -90 and 90 (the north and south poles) or exclude them.

    Longitudes
    ----------
    The range of longitudes is [-180, 180].
    """
    def __init__(self, array=None, lat=None, lon=None, name=None):
        
        # The preference is to use the grid from a specified existing
        # DataArray.
        if array is not None:
            if type(array) is not xr.DataArray:
                msg = "The parameter array must be an xarray DataArray."
                raise TypeError(msg)

            self._lats = array.lat.values
            self._lons = array.lon.values

        # Specifying the latituds and longitudes explicitly is ultimately the
        # easiest and most reliable way, due primarlly to the redundancy:
        # [-90, 0, 90] and (-45, 45] are both grids with 90-degree widths.
        else:
            self._lats = lat
            self._lons = lon

        # Determining a name from the latitudes and longitudes is complicated
        # from too many choices for how to form the name.  Best is to let the
        # the definer specify a name.
        if name is not None:
            self.name = name
        else:
            self.name = self._name()

    # The default name is GRID_###, where ### is the height of the latitude
    # spacing in tenths of a degree.  Most grids are defined such that the
    # spacing between lines of latitude and longitude are the same.
    def _name(self):
        latitude_range = self._lats[-1] - self._lats[0]
        
        # Subtract 1 from the length because [-90, 0, 90] has three latitudes
        # defined, but two spaces between the latitudes.
        latitude_height = latitude_range/(len(self._lats) - 1)
        if 90 in self._lats:
            return "GRID_{:03d}_{}".format( int(10*latitude_height),
                                            len(self._lats) )
        else:
            return "GRID_{:03d}".format( int(10*latitude_height) )

    @property
    def lat(self):
        return self._lats

    @property
    def lon(self):
        return self._lons

    @property
    def latlen(self):
        return len(self._lats)

    @property
    def lonlen(self):
        return len(self._lons)

    @property
    def cartesian(self):
        ret = cartesian(( [self._lats, self._lons] ))
        return ret
    
    # An iterator to iterate through the grid points.
    def grid_points(self):
        for i in range(0, self.latlen):
            for j in range(0, self.lonlen):
                yield i,j

    # Create a string nxm, where n (m) is the distance in degrees between lines
    # of latitude (longitude).
    def __str__(self):
        # latitudes may or may not exclude the pole.  The numerator for the
        # latitude calculation must consider this.  Furthermore, the because
        # the latitudes have end points, the number of spaces is one less than
        # the number of latitudes.
        width_lat = (self._lats[-1] - self._lats[0])/(self.latlen - 1)

        # The longitudes may wrap, or not.  Typically, for small regions, the
        # longitude does not wrap.  Here, if the distance between the two
        # longitude extremes is close to the spacing, we assume the longitudes
        # wrap.  This is not perfect.
        wrap_space = self._lons[0] + 360 - self._lons[-1]
        common_space = self._lons[1] - self._lons[0]
        wrap_case = (wrap_space < 1.1*common_space)
        if wrap_case: 
            width_lon = 360.0/self.lonlen
        else:
            width_lon = (self._lons[-1] - self._lons[0])/(self.lonlen - 1)
        
        # Let Python pick the number of decimal places.  If there are many,
        # that usually means a mistake has been made.
        ret = "{}x{}".format(width_lat, width_lon)
        return ret


# Predefined grids.  The convention is GRID_### where ### represents the
# width of the cell in tenths of degrees.  For the grids that do include
# the poles, GRID_###_# where the second number indicates the number of
# latitudes
GRID_025 = Grid(lat=np.linspace(-88.75, 88.75, 72),
                lon=np.linspace(-178.75, 178.75, 144),
                name='GRID_025')
GRID_100 = Grid(lat=np.linspace(-85, 85, 18),
                lon=np.linspace(-175, 175, 36),
                name="GRID_100")
GRID_300 = Grid(lat=np.linspace(-75, 75, 6),
                lon=np.linspace(-165, 165, 12),
                name='GRID_300')


# Thanks to hernamesbarbara on github for this function.
#
# Googling did not find a built-in function, nor a function in the Numpy and
# SciPy libraries that produced a cartesian product of lists, where each
# element is a list instead of a tuple.  This is odd, because all the
# interpolation functions in SciPy require the inputs to be in this form.
# Seeming, this obligates the user to create this function on his own.
def cartesian(arrays, out=None):
    '''
    Generate a cartesian product of input arrays.
    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.
    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.
    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])
    '''

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = n / arrays[0].size
    out[:,0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m,1:])
        for j in xrange(1, arrays[0].size):
            out[j*m:(j+1)*m,1:] = out[0:m,1:]
    return out


# For a list of variables, each represented as an xarray DataArray, compute
# the longitude, latitude lattice (grid) that is the dimension-wise union of
# all the coordinate dimensions. 
def union_coords(variables):
    '''
    For each dimension (i.e. lat, lon) form the union of points over all
    variables.  This function presumes that the names of the dimensions are
    lat and lon.
    
    :return a dictionary of sorted lists, one for each dimension.
    '''
    lat = set([])
    lon = set([])
    for v in variables:
        lat = lat | set(v['lat'].values)
        lon = lon | set(v['lon'].values)

    ret = {'lon': sorted(list(lon)), 'lat': sorted(list(lat))}
    return ret


# The following function is a second attempt.  It accomplishes the regridding 
# by iterating on all four dimensions.  It assumes that the plev and time
# coordinates will be identical for all datasets -- obviously not a safe
# assumption.
#
# The method should be replace by the regridding API provided in ESMFPy at
# www.earchsystemmodeling.org (part of ESGF).  Presumably it's faster and more
# likely to be correct.  Also, the ESMFPy API supports parallelizing the
# regridding operation.
#
def regrid(variables, lattice='union', tl=None, pl=None):

    # At present, only one method of prescribing the destination lattice is
    # supported.  That is, the destination lattice if formed by the union over
    # all lattices in the input list of variables.
    if 'union' == lattice:
        c = union_coords(variables)
        coords_lat = c['lat']
        coords_lon = c['lon']
    
    # Simple, very low-resolution lattice for development and testing.
    # Gridlines are every 30 degrees apart.
    elif 'latlon_30' == lattice:
        coords_lat = np.linspace(-90, 90, 7)
        coords_lon = np.linspace(0, 330, 12)
        
    # A low-resolution grid for testing.  This is not so low that there are
    # only a few simplices, yet it's not too big so that it's reasonably
    # fast.
    elif 'latlon_5' == lattice:
        coords_lat = np.linspace(-90, 90, 37)
        coords_lon = np.linspace(0, 355, 72)

    elif 'latlon_1' == lattice:
        coords_lat = np.linspace(-90, 90, 181)
        coords_lon = np.linspace(0, 359, 360)

    else:
        errMsg = "Lattice %s is not supported." % (lattice)
        raise NotImplementedError(errMsg)

    # The destination lattice won't change.  Now is a good time to build the
    # indexing structure on it.
    coords = cartesian(( [coords_lat, coords_lon] ))
#    coordtree = KDTree(coords)

    # This point starts the process of regridding.
    newvars = []
    for var in variables:
        
        # Establish the levels for time and plev at which the variable is
        # interpolated on the new lattice.  The time to complete this procedure
        # scales linearly with the number of these variables.  Therefore, allow
        # the user to specify exactly what's needed.
        if tl == None:
            time_levels = np.arange(len(var['time'].values))
        else:
            time_levels = tl
        if pl == None:
            plev_levels = np.arange(len(var['plev'].values))
        else:
            plev_levels = pl

        # These variables are
        # all presumed to be defined on a four-dimensional grid: lon, lat,
        # plev, time.  It is further assumed that time and plev don't need
        # to be regrid, because all the variables are defined for the same
        # values of those dimensions.
        newdata = np.empty( (len(time_levels), len(plev_levels), len(coords_lat), len(coords_lon)) )
        newdata[:] = np.NaN
        
        # This aspect of Python cost me an afternoon.  if you create an
        # iterator like this:
        #  myiterator = enumerate(var['plev'].values[plev_levels])
        # ...then that iterator can only be used once.  Once the code
        # iterfaces through it's values, it's done.  So nested loops using
        # these DO NOT WORK.
        for t, time_ in enumerate(var['time'].values[time_levels]):
            for p, plev in enumerate(var['plev'].values[plev_levels]):
                
                # Impose a Delaunay triangulation and an indexing structure
                # on the variable.
                varcoords = cartesian(( [var['lat'], var['lon']] ))
                vartri = Delaunay(varcoords)

                # Flatten the variable on lat and lon.
                # CHECK THAT var[time,plev].values.flatten()
                # has the same shape (N,2) as varcoords
                # and that they are in the same order.
                x = var[t,p].values.flatten()
                
                # Loop on the destination lattice dimensions.
                numcoords = len(coords)
                print "[Time: %s][Plev: %s] %s(%s points)" % (time_, plev, '-'*int(numcoords/1000), numcoords)
                print "[Time: %s][Plev: %s] " % (time_, plev),
                
                tmp = np.empty(len(coords))
                for i, lattice_point in enumerate(coords):
                    n = vartri.find_simplex(lattice_point)
                    pts = vartri.simplices[n]
                    spts = vartri.points[pts]
                    
                    f = LinearNDInterpolator(spts, x[pts])
                    tmp[i] = f(lattice_point)
                    
                    if (i + 1)%1000 == 0:
                        sys.stdout.write(".")
                print ""
                
                # Reshape the tmp array to organize it by lat, lon.
                tmp = np.reshape( tmp, (len(coords_lat), len(coords_lon)) )
                newdata[t,p,:,:] = tmp
                
        # Package the new variable, defined on the destination lattice, into an
        # xarray DataArray.
        foo = xr.DataArray(newdata,
                           coords=[var['time'].values[time_levels],
                                   var['plev'].values[plev_levels],
                                   coords_lat,
                                   coords_lon],
                           dims=['time', 'plev', 'lat', 'lon'],
                           name=var.name,
                           attrs=var.attrs)

        newvars.append(foo)


    return newvars

def simple_regrid(var, grid=None, likevar=None, progressbar=None):

    # Check for regrid capability.  If there are more than three dimensions,
    # it's not feasible yet.  If there are exactly three, the third must be
    # time.
    have_time_dim = (len(var.shape) == 3 and 'time' in var.dims)

    if grid is not None:
        to_coords = grid
    elif likevar is not None:
        to_coords = Grid(array=likevar)
    else:
        to_coords = GRID_025
    
    # Display the ranges involved in the regrid, for confidence.
    from_coords = Grid(array=var)
    print "Regridding from {0} to {1}.".format(str(from_coords),
                                               str(to_coords))

    # Impose a Delaunay triangulation and an indexing structure
    # on the variable.
    varcoords = from_coords.cartesian
    vartri = Delaunay(varcoords)

    # Create a DataArray object with the new shape filled with np.NaNs.  This
    # will be filled with values interpolation from the variable var.
    if have_time_dim:
        blankdata = np.empty((len(var.time),
                              to_coords.latlen,
                              to_coords.lonlen))
        blankdata.fill(np.NaN)
        newvar = xr.DataArray(blankdata,
                              name=var.name,
                              attrs=var.attrs,
                              coords={'time': var.time,
                                      'lat': to_coords.lat,
                                      'lon': to_coords.lon},
                              dims=['time', 'lat', 'lon'])
    else:
        blankdata = np.empty((to_coords.latlen, to_coords.lonlen))
        blankdata.fill(np.NaN)
        newvar = xr.DataArray(blankdata,
                              name=var.name,
                              attrs=var.attrs,
                              coords={'lat': to_coords.lat,
                                      'lon': to_coords.lon},
                              dims=['lat', 'lon'])
    
    # Set the missing_value attribute to 'NaN (numpy)'.  Set the grid attribute
    # to the new grid.
    newvar.attrs['missing_value'] = 'nan'
    newvar.attrs['grid'] = str(to_coords)

    # Show progress at the latitudes.  Otherwise it's too many.
    if progressbar is not None:
        progressbar.start(to_coords.latlen*to_coords.lonlen)

    # Iterate the new variable's grid, calculating the value from an
    # interpolation of the simplices in the original variable.
    # FIX ME: The interpolation function is calculated for as many points of
    # the new variable that fall in a single simplex.  It only needs to be
    # calculated once per simplex.
    for i,j in to_coords.grid_points():
        
        # These steps produce the i-th simplex (triangle) in the variable.
        lattice_point = [to_coords.lat[i], to_coords.lon[j]]
        simplex_number = vartri.find_simplex(lattice_point)
        if simplex_number >= 0:
            simplex_points = vartri.simplices[simplex_number]
            simplex = vartri.points[simplex_points]
            
            # These steps produce the n-values of the variable for the
            # n-simplex.  Since the simplices are triangles, these steps
            # produce three values.
            if have_time_dim:
                for t in range(0, len(var.time)):
#                for t in range(0, 3):
                    vals = []
                    for k, vertex in enumerate(simplex):
                        val = var.sel(time=var.time[t],
                                      lat=vertex[0],
                                      lon=vertex[1])
                        vals.append(val)
        
                    # These steps produce the function f that calculates the
                    # interpolated value anywhere in the simplex (triangle),
                    # and then calculates that value at the lattice point, and
                    # assigns it.
                    f = LinearNDInterpolator(simplex, vals)
                    x = f(lattice_point)
                    newvar[t, i, j] = x 
            else:
                vals = []
                for k, vertex in enumerate(simplex):
                    val = var.sel(lat=vertex[0], lon=vertex[1])
                    vals.append(val)
    
                # These steps produce the function f that calculates the
                # interpolated value anywhere in the simplex (triangle), and
                # then calculates that value at the lattice point, and assigns
                # it.
                f = LinearNDInterpolator(simplex, vals)
                x = f(lattice_point)
                newvar[i, j] = x 
    
        # Show progress.
        if progressbar is not None:
            msg = ("Calculated values for ({:2.3f}, {:2.3f}).").format(
                to_coords.lat[i], to_coords.lon[j])
            progressbar.update(msg)

    return newvar

def standardize_latlon(var):
    """Standardizes the latitudes and longitudes.
    
    Returns the data in a DataArray where the latitudes range from [-90,90] and
    the longitudes range from (-180, 180].
    """
    # Ensure the variable order is lat,lon, time.
    retvar = var.transpose('lat', 'lon', 'time')
    
    if retvar.lat[1] - var.lat[0] < 0:
        data = retvar[::-1,:,:]
        lats = retvar.lat[::-1]
    else:
        data = retvar[:,:,:]
        lats = retvar.lat

    need_longitude_roll = (max(retvar.lon) > 180)
    if need_longitude_roll:
        lons = np.mod(retvar.lon + 180, 360) - 180
    else:
        lons = retvar.lon
    
    retvar = xr.DataArray(data,
                          name=var.name,
                          attrs=var.attrs,
                          coords={'lat': lats, 'lon': lons, 'time': var.time},
                          dims=['lat', 'lon', 'time'])
    
    # The negative longitudes may be at the nd of the lon array.  This moves
    # them to the front.
    if need_longitude_roll:
        negvals = np.where(retvar.lon.values < 0)
        if negvals[0].size > 0:
            offset = negvals[0][0]
            retvar = retvar.roll(lon=offset)

    return retvar

def transpose_var(data):
    """Determines if the data in an Xarray DataArray is transposed.
    
    Occasionally, the data in a dataset is organized with the longitude
    coordinate first and the latitude coordinate second.  This is causing
    problems with the matplotlib contourf and addcyclic methods.
    
    This function determines the lon dimension by comparing the shape of the
    data to the lengths of the latitude and longitude coordinates.  If the
    shape is such that the longitude is first, the data is transposed and the
    new DataArray is returned.
    """
    data_shape = data.shape
    if data_shape[0] == len(data.lon.values):
        # Longitude is first.  It needs to be transposed.
        var_name = data.name
        var_data = data.values
        new_var_data = np.transpose(var_data)
        new_array = xr.DataArray(new_var_data,
                                 coords=[data.lat.values, data.lon.values],
                                 dims=['lat', 'lon'])
        new_array.name = var_name
        return new_array
    else:
        return data

def get_urs_file(url):
    username = 'godfrey4000'
    password = 'J#bunan0'
#    the_url = 'https://disc2.gesdisc.eosdis.nasa.gov:443/opendap/TRMM_L3/TRMM_3B42.7/1998/001/3B42.19980101.03.7.HDF'
    session = setup_session(username, password, check_url=url)
#    dataset = open_url(the_url, session=session)
    ds = xr.open_dataset(url, decode_cf=False, engine='pydap', session=session)
    return ds

def gaussian_smooth(var, sigma):
    """Apply a filter, along the time dimension.
    
    Applies a gaussian filter to the data along the time dimension.  if the
    time dimension is missing, raises an exception.  The DataArray that is
    returned is shortened along the time dimension by sigma, half of sigma on
    each end.
    
    The width of the window is 2xsigma + 1.
    """
    if type(var) is not xr.DataArray:
        raise TypeError("First argument must be an Xarray DataArray.")
    if 'time' not in var.dims:
        raise IndexError("Time coordinate not found.")

    # The convolution window must have the same number of dimensions as the
    # variable.  The length of every dimension is one, except time, which is
    # 2xsigma + 1.
    var_dimensions = np.ones( len(var.coords), dtype=np.int )
    timepos = var.dims.index('time')
    var_dimensions[timepos] = 2*sigma + 1
    
    # Use a normalized gaussian so the average of the variable does not change.
    gausswin = gaussian(2*sigma + 1, sigma)
    gausswin = gausswin/np.sum(gausswin)

    # The window series used in the convolve operation is the gaussion for the
    # time dimension and a singleton zero for the other dimensions.  This way
    # the multidimension covolve is:
    #
    #    g(m,n,...) = \sum_k \sum_l ... f[k,l,...]h[k-m]\delta_l0...
    #
    timeslice_specification = [0 for x in range(len(var.coords))]
    timeslice_specification[timepos] = slice(None)
    win = np.zeros(var_dimensions)
    win[timeslice_specification] = gausswin
    
    # The third parameter 'same' specifies a return array of the same shape as
    # var.
    out = convolve(var, win, 'same')
    outda = xr.DataArra(out,
                        coords=var.coords,
                        dims=var.dims)
    outda.attrs = var.attrs

    # Append "(Gaussian filtered: sigma = ###" to the end of th variable name.
    newname = "{0} (Gaussian filtered: sigma = {1})".format(var.name, sigma)
    outda.name = newname
    return outda
