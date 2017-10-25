'''
Created on Sep 29, 2017

@author: neil
'''
import xarray as xr

# Utility method that standardizes the title and other descriptive text from
# a Dataset or DataArray.
def extract_plot_titles(ds):
    
    # Default values.  These will get returned if they're not set by the
    # routines that follow.
    ret = {'title': 'Untitled',
           'name': ds.name,
           'units': '???'}

    have_title = ('title' in ds.attrs)
    have_long_name = ('long_name' in ds.attrs)
    have_standard_name = ('standard_name' in ds.attrs)
    have_units = ('units' in ds.attrs)

    # For the title, the order of preference is title, long_name.
    if have_title:
        ret['title'] = ds.attrs['title']
    elif have_long_name:
        ret['title'] = ds.attrs['long_name']

#    # For an Xarray DataArray, the name is the name property of the
#    # DataArray.
#    ret['name'] = ds.name

    if have_units:
        ret['units'] = ds.attrs['units']

    return ret