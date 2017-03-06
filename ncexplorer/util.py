'''
Created on Dec 28, 2016

@author: neil
'''
import sys
import numpy as np
import xarray as xr
from scipy.spatial import KDTree, Delaunay
from scipy.interpolate import LinearNDInterpolator


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
