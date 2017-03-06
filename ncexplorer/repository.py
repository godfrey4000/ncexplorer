'''
Created on Dec 21, 2016

@author: neil
'''
from pyesgf.logon import LogonManager
from pyesgf.search import SearchConnection
import xarray as xr
import numpy as np
from urlparse import urlparse

from config import CFG_ESGF_NODE
from config import CFG_ESGF_SEARCH_NODE
from config import CFG_ESGF_OPENID_NODE

# The authenticator classes make it possible to use different authentication
# methods with different repositories.  It also allows for trivial
# authentication methods for use in testing and development.
class Authenticator(object):
    '''The Authenticator handles login and logout to repositories.'''
    def __init__(self, app):
        '''
        The authenticator requires access to the parent application so that
        it can ask the application to prompt and collect the username and
        password.
        '''
        self._app = app

        # Setup the login manager.  This will depend on the repository.
        self._set_lm()

    def login(self):
        return False

    def logout(self):
        pass

# Standard class for ESGF authentication.
class OpenIDAuthenticator(Authenticator):
    '''Authenticates to an ESGF node using open ID.'''
    
    # Use the login manager from the pyesgf library.
    # NOTE: This library uses 'logon/logoff' everywhere.  The convention
    # used throughout this application is 'login/logout'
    def _set_lm(self):
        self._lm = LogonManager()
        self._username = None
        self._password = None
        
        # Ensure the user is logged out initially.
        self._lm.logoff()

    def login(self):
        if None == self._username or None == self._password:
            creds = self._app.set_login_creds()
            self._username = creds['username']
            self._password = creds['password']
        
        oid_node = CFG_ESGF_OPENID_NODE
        oid = oid_node + '/' + self._username

        # FIX ME: Do we need bootstrap=True/
        self._lm.logon_with_openid(oid, self._password, bootstrap=True)
        return (self._lm.is_logged_on())

    def logout(self):
        self._lm.logoff()

# Trivial authentication with hardcoded username and password.
class TrivialAuthenticator(OpenIDAuthenticator):
    def _set_lm(self):
        self._lm = LogonManager()
        self._username = 'godfrey4000@gmail.com'
        self._password = 'J#bunan0'
        self._lm.logoff()


# An NCXRepository is an internet server that houses NetCDF files and supports
# OpenDAP.         
class NCXRepository(object):
    '''
    Interface class for searching archives of NetCDF data (repositories),
    retrieving data from the repository, and authenticating to the
    repository if required.
    '''
    def __init__(self):

        # Set the ID.  This is a unique constant the serves as the key in the
        # applications dictionary of repositories.
        self.id = self._set_id()

    # Subclasses implementing this interface must implement these methods:
    def _set_id(self):
        '''Set the repository ID to a constant unique to repositories'''
        pass
    def _set_authenticator(self):
        '''
        Set the class that will implement authentication  (logging in and
        logging out).
        '''
        pass
    def _search(self, log, progressbar):
        pass
    def _retrieve_data(self, log, progressbar):
        pass

    # The repository will have occasion to call the parent application's
    # methods.  Any repository method that does this can't be called until
    # this method as set the _app property.
    def set_app(self, app):
        '''Set the _app property to the parent application.'''
        self._app = app

        # Let the subclass choose the authentication method.
        self._authenticator = self._set_authenticator()

    # The search parameters are set here, at the level of the base class, in an
    # attempt to standardize the search parameters across repositories.  This
    # might be too ambitious.
    def set_search_params(self, **kwargs):
        '''Set the search parameters for a search.'''
        self._search_params = kwargs

    def search(self, log, progressbar):
        '''
        Interface method to conduct a search using the preset search parameters.
        '''
        self._search(log, progressbar)

    def retrieve_data(self, log, progressbar):
        '''
        Interface method to retrieve the data specified in the OpenDAP URLS
        that have been saved.
        '''
        return self._retrieve_data(log, progressbar)

    def urls(self):
        return self._opendap_urls


# Implementation of the NCXRepository class for the ESGF servers.
class NCXESGF(NCXRepository):
    '''
    This class implements the NXSearch interface for ESGF.
    '''
    def _set_id(self):
        self.id = CFG_ESGF_NODE

    def _set_authenticator(self):
#        auth = TrivialAuthenticator(self._app)
        auth = OpenIDAuthenticator(self._app)
        return auth

    # Build a list of OpenDAP URLs that provide 
    def _search(self, log, progressbar):
        '''
        Execute the search using the pyesgf library, which uses the ESGF
        search API.  Stores a list of OpenDAP URLs as resources.
        '''
        esgf_node = CFG_ESGF_SEARCH_NODE
        conn = SearchConnection(esgf_node, distrib=True)
        ctx = conn.new_context(**self._search_params)
        hit_count = ctx.hit_count

        # Each search clears the files from before.  The pyesgf library allows
        # for searches to be refined.  Consider utilizing that capability here.
        progressbar.start(hit_count)
        self._opendap_urls = []
        self._variable = self._search_params['variable']
        ds = ctx.search()
        i = 1
        for dsresult in ds:
            files = dsresult.file_context().search(variable=self._variable)
            msg = "Searching %s of %s.  %s files." % (i, hit_count, len(files))
            log.debug(msg)
        
            for f in files:
                self._opendap_urls.append(f.opendap_url)
            i += 1
            progressbar.update(msg)

    def _retrieve_data(self, log, progressbar):
        '''
        Execute the search using the pyesgf library, which uses the ESGF
        search API.  Then retrieve the data and make it available to the
        application as an xarray Dataset object.
        '''
        self._authenticator.login()

        temp_ds = []
        l = len(self._opendap_urls)
        
        # Add two to the progress bar.  One for just starting, and another
        # for when it's all finished.  Without these extra, the user can be
        # looking at a blank progress bar for the whole time, since _clean()
        # takes so long.
        progressbar.start(2*l)
        for f in self._opendap_urls:

            # FIX ME: Explore cheaper ways to determine if the file contains
            # the requested variable.  This implementation downloads the
            # entire file, and then discards it. 
            x = xr.open_dataset(f, decode_cf=False)
            if self._variable in x:
                
                o = urlparse(f)
                filename = o.path.split('/')[-1]
                msg = "Cleaning: [{0}] {1}.".format(o.netloc, filename)
                log.debug(msg)
                progressbar.update(msg)

                # Normalize it.
                # FIX ME: Consider moving this to another place.  This
                # operation is the biggest bottleneck of this searching and
                # retrieving data.
#                self._clean(x)
             
                temp_ds.append(x)
                msg = "Saved: [{0}] {1}".format(o.netloc, filename)
                log.debug(msg)
            progressbar.update(msg)

        # Don't stay logged on.
        self._authenticator.logout()

        # Return the list of xarray Dataset objects.  The Dataset data
        # structure can't hold the datasets thus far collected because, in
        # general, their coordinates will be defined on different lattices.
        return temp_ds

    # This method contains a body of routines for normalizing the data
    # coming from ESGF
    #     (1) Datasets supply a real number (typically 1e+20) that is to be
    #         interpreted a missing values.  This causes problems with
    #         plotting utilities and interpolation algorithms
    #     (2) The time values differ from dataset to dataset, while the
    #         intervals do not.  With different values, arithmetic on datasets
    #         fails.
    def _clean(self, ds):
        '''
        Cleans the dataset from ESGF.  The dataset passed as a parameter is
        mutable so it gets modified.
        '''
        # Replace missing values with numpy's NaN.  The missing value is
        # usually 1e+20, but values can be like 1.0000002e+20, which is
        # different.  Ergo the inequality.
        for var in ds.data_vars.itervalues():
            if 'missing_value' in var.attrs:
                MDV = var.missing_value
                var.values[var.values >= MDV] = np.NaN

        # FIX ME: This should check if the time type is monClim.  Also, check
        # to see if the first value should be 15.5.  In the meantime, so that
        # the value is at the midpoint of the interval, shift everything by
        # half.
        time0 = ds.coords['time'][0]
        delta = 0.5*(ds.coords['time'][1] - ds.coords['time'][0])
        ds.coords['time'] -= time0
