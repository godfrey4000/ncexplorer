'''
Created on Dec 21, 2016

@author: neil
'''
import os
import ntpath
from webob.exc import HTTPError
from pyesgf.logon import LogonManager
from pydap.cas.esgf import setup_session
from pyesgf.search import SearchConnection
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
from dateutil import relativedelta
from urlparse import urlparse

from ncexplorer.config import CFG_ESGF_NODE
from ncexplorer.config import CFG_ESGF_SEARCH_NODE
from ncexplorer.config import CFG_ESGF_OPENID_NODE
from ncexplorer.util import get_urs_file
from fileinput import filename


# The authenticator classes make it possible to use different authentication
# methods with different repositories.  It also allows for trivial
# authentication methods for use in testing and development.
class Authenticator(object):
    """The Authenticator handles login and logout to repositories."""
    def __init__(self, app):
        """
        The authenticator requires access to the parent application so that
        it can ask the application to prompt and collect the username and
        password.
        """
        self._username = None
        self._password = None
        self._lm = None
        self._app = app
        self.session = None

        # Setup the login manager.  This will depend on the repository.
        self._set_lm()

    def username(self):
        """Return the username"""
        return self._get_username()

    # This method must be overriden by the subclass.
    def _set_lm(self):
        pass
    def _get_username(self):
        return self._username

    def login(self):
        return False

    def logout(self):
        pass

# Standard class for ESGF authentication.
class OpenIDAuthenticator(Authenticator):
    """Authenticates to an ESGF node using open ID."""
    
    def _oid(self):
        return CFG_ESGF_OPENID_NODE + '/' + self._username

    # The OpenID has a long server name component and is easy to forget.
    # Making it accessible as a property is often useful.
    def _get_username(self):
        return self._oid()

    # Use the login manager from the pyesgf library.
    # NOTE: This library uses 'logon/logoff' everywhere.  The convention
    # used throughout this application is 'login/logout'
    def _set_lm(self):
        self._lm = LogonManager()
#        self._username = None
#        self._password = None

        # Ensure the user is logged out initially.
        self._lm.logoff()

    def login(self, url):
        if self._username is None or self._password is None:
            creds = self._app.set_login_creds()
            self._username = creds['username']
            self._password = creds['password']

        oid = self._oid()

#        # FIX ME: Do we need bootstrap=True/
#        self._lm.logon_with_openid(oid, self._password, bootstrap=True)
#        return self._lm.is_logged_on()
        self.session = setup_session(oid, self._password, check_url=url)
        return True
        

    def logout(self):
        self._lm.logoff()


class URSAuthenticator(Authenticator):
    
    def login(self):
        pass
        
# Trivial authentication with hard coded user name and password.  It uses the
# OpenID authentication, but eliminates typing in the password a zillion
# times.
class TrivialAuthenticator(OpenIDAuthenticator):
    """Just for testing.  Do not use."""
    def _set_lm(self):
        self._lm = LogonManager()
        self._username = 'godfrey4000@gmail.com'
        self._password = 'J#bunan0'
        self._lm.logoff()


# This class does no authentication at all.  It's used for local disk access.
class NullAuthenticator(Authenticator):
    """Performs no login function."""
    # The parent class returns False.  The intention is that login fails unless
    # the sub class implements a login capability.  In this class, login will
    # always work.  Presumably, permissions are set on the directory.
    def login(self):
        return True

    def logout(self):
        pass


# The parent class for all repositories..
class NCXRepository(object):
    """
    Interface class for searching archives of NetCDF data (repositories),
    retrieving data from the repository, and authenticating to the
    repository if required.
    """
#    shortname = None
    
    def __init__(self, repospec):

        self._app = None
        self._authenticator = None
        self._search_params = None
        self._urls = None

        # Set the ID.  This is a unique constant the serves as the key in the
        # applications dictionary of repositories.
        self._repo_type = repospec['type']
        self._repo_parameters = repospec['parameters']

        # The structure of the repository parameters is different for different
        # repository classes.  So the sub class sets the id.
        self.id = self._set_id()
        
#        # Repositories should set a short name.  If this hasn't been set, raise
#        # and exception so it can be addressed.
#        if self.shortname is None:
#            msg = ("Repository {}: attribute short name not defined.  " +
#                   "Repository subclasses must assign the shortname " +
#                   "attribute").format(self.id)
#            raise NameError(msg)

    def username(self):
        """Return the username used by the authenticator."""
        return self._authenticator.username()

    # Subclasses implementing this interface must implement these methods:
    def _set_id(self, repospec):
        '''Set the repository ID to a constant unique to repositories'''
        pass
    def _set_authenticator(self):
        """
        Set the class that will implement authentication  (logging in and
        logging out).
        """
        pass
    def _search(self, log, progressbar):
        pass
    def _retrieve_data(self, log, progressbar, files):
        pass

    # The repository will have occasion to call the parent application's
    # methods.  Any repository method that does this can't be called until
    # this method as set the _app property.
    def set_app(self, app):
        """Set the _app property to the parent application."""
        self._app = app

        # Let the subclass choose the authentication method.
        self._authenticator = self._set_authenticator()

    def push(self, progressbar, ds):
        """Push the dataset from the client to the repository."""
        return self._push(progressbar, ds)

    def retrieve_data(self, log, progressbar, files):
        """Retrieve the data specified in the saved OpenDAP URLS."""
        return self._retrieve_data(log, progressbar, files)

    # The search parameters are set here, at the level of the base class, in an
    # attempt to standardize the search parameters across repositories.  This
    # might be too ambitious.
    def set_search_params(self, **kwargs):
        """Set the search parameters for a search."""
        self._search_params = kwargs

    def search(self, log, progressbar=None):
        """Conduct a search using the preset search parameter."""
        self._search(log, progressbar)

    def urls(self):
        """Return the saved URLs"""
        return self._list_urls()
    
    def _list_urls(self):
        return self._urls


class NCXURS(NCXRepository):
    
    # A generator that returns a pydap proxy for all the files in the
    # directory of the URS NASA Earthdata server.
    def _genfiles(self):
        # The Earthdata starts in 1997 and goes to roughly the present.  The
        # range here stops at the end of 2016 so as to not introduce any bias
        # in seasons.
        onemonth = relativedelta.relativedelta(months=1)
        cur_dt = datetime.strptime('1998-01-01 00:00:00', '%Y-%d-%m %H:%M:%S')
        end_dt = datetime.strptime('2017-01-01 00:00:00', '%Y-%d-%m %H:%M:%S')
        while cur_dt < end_dt:
            
            # There is a peculiarity in the file naming convention.  The first
            # file of every day is named with with current day, but in the
            # directory for the previous day.
            fyear = cur_dt.year
            fmonth = cur_dt.month
                    
            filename = "%04d/3B43.%04d%02d01.7.HDF" % (
                fyear, fyear, fmonth)
            filename_a = "%04d/3B43.%04d%02d01.7A.HDF" % (
                fyear, fyear, fmonth)
            remotefile = (self._repo_parameters['server'] +
                          self._repo_parameters['directory'] +
                          filename)
            remotefile_a = (self._repo_parameters['server'] +
                          self._repo_parameters['directory'] +
                          filename_a)

            # Retrieve the file using the pydap library, implemented in the
            # util module.
            try:
                ds = get_urs_file(remotefile)
            except HTTPError:
                print "{0}: 404.".format(filename)
                try:
                    ds = get_urs_file(remotefile_a)
                except HTTPError:
                    print "{0}: 404.".format(filename_a)
                    cur_dt = cur_dt + onemonth
                    continue
            yield ds
            
            # Advance to the next day.
            cur_dt = cur_dt + onemonth

    def _set_id(self):
        # FIXME:  Tthis is a total kludge.
        return 'URS'
    
    def _set_authenticator(self):
        auth = URSAuthenticator(self._app)
        return auth
    
    def _search(self, log, progressbar):
        # This response simply adversises the form of the files that are
        # available on this repository.
        self._urls = ['3B43.[YYYYMMDD].[hh].7.HDF']
                        
    def _retrieve_data(self, log, progressbar, files):
        
#        temp_ds = []
#        for i, remotefile in files:
#            url = self.base_url + remotefile
#            ds = get_urs_file(url)
#            temp_ds.append(ds)
#        
#        return temp_ds
        return self._genfiles
        
            
# Implementation of the NCXRepository class for the ESGF servers.
class NCXESGF(NCXRepository):
    """Implements the NXSearch interface for ESGF."""
    
    def _set_id(self):
        if self._repo_type != 'esgf':
            msg = ("NCXESGF repository class cannot be created with a " +
                   "specification type {0}.".format(self._repo_type))
            raise TypeError(msg)

        node = self._repo_parameters['node']        
        return 'ESGF'

    # TODO: This is set to the trivial authenticator, waiting for a
    # means to collect user name and password from the web GUI and the
    # desktop GUI.
    def _set_authenticator(self):
        auth = TrivialAuthenticator(self._app)
#        auth = OpenIDAuthenticator(self._app)
        return auth

    # Build a list of OpenDAP URLs that that match the the search string
    # contained in self._search_params.
    def _search(self, log, progressbar):
        """Execute the search using the pyesgf library.
        
        Execute the search using the pyesgf library, which uses the ESGF
        search API.  Stores a list of OpenDAP URLs as resources.
        """
        # FIXME: This should be part of the initialization.
        # The urls() method must return a list.
        self._urls = {}

        # Can't allow an empty search string; the repository is too big and
        # will return too many files.  An empty search string is legal because
        # local repositories are small, and an empty string asks for all the
        # files.
        if len(self._search_params) == 0:
            return

        esgf_node = self._repo_parameters['search_node']
        conn = SearchConnection(esgf_node, distrib=True)
        ctx = conn.new_context(**self._search_params)
        hit_count = ctx.hit_count

        # Each search clears the files from before.  The pyesgf library allows
        # for searches to be refined.  Consider utilizing that capability here.
        if hit_count > 0:
            progressbar.start(hit_count)
#            self._variable = self._search_params['variable']
            datasets = ctx.search()
            i = 1
            for dsresult in datasets:
                if 'variable' in self._search_params:
                    remotefiles = dsresult.file_context().search(
                        variable=self._search_params['variable'])
                else:
                    remotefiles = dsresult.file_context().search()
                msg = "Searching %s of %s.  %s files." % (i, hit_count, len(remotefiles))
                log.debug(msg)
    
                for remotefile in remotefiles:
                    urlobj = urlparse(remotefile.opendap_url)
                    filename = urlobj.path.split('/')[-1]
                    self._urls[filename] = remotefile.opendap_url
                i += 1
                progressbar.update(msg)

    # Not permitted to push files to the ESGF repositoris.
    def _push(self, progressbar, ds):
        msg = "ESGF repository is read only.  Pushing data not permitted."
        raise TypeError(msg)

    def _retrieve_data(self, log, progressbar, files):
        """Retrieve data using the pyesgf library.

        Execute the search using the pyesgf library, which uses the ESGF
        search API.  Then retrieve the data and make it available to the
        application as an xarray Dataset object.
        """
#        login_successful = self._authenticator.login()
#        if not login_successful:
#            self._app.logger.warn("Failed to login.")
#        session = self._authenticator.session

        temp_ds = []
        url_length = len(files)
        session = None

        # Add two to the progress bar.  One for just starting, and another
        # for when it's all finished.  Without these extra, the user can be
        # looking at a blank progress bar for the whole time, since _clean()
        # takes so long.
        progressbar.start(2*url_length)
        for i, remotefile in files:

            # The remotefile is just the filename, which is nicer for display.
            # Need the full url.
            url = self._url_from_file(remotefile)
            if session is None and self._authenticator.login(url):
                session = self._authenticator.session
            
            if session is not None:
                xdataset = xr.open_dataset(url,
                                           decode_cf=False,
                                           engine='pydap',
                                           session=session)
                msg = "Cleaning: {0}.".format(remotefile)
            else:
                msg = "Login failed."
            log.debug(msg)
            progressbar.update(msg)

#            # Normalize it.
#            # FIX ME: Consider moving this to another place.  This
#            # operation is the biggest bottleneck of this searching and
#            # retrieving data.
#                self._clean(x)

            temp_ds.append(xdataset)
            msg = "Retained: {0}".format(filename)
            log.debug(msg)
                
            progressbar.update(msg)

        # Don't stay logged on.
        self._authenticator.logout()

        # Return the list of xarray Dataset objects.  The Data_repospecset data
        # structure can't hold the datasets thus far collected because, in
        # general, their coordinates will be defined on different lattices.
        return temp_ds

    # FIXME: 
    def _url_from_file(self, fn):
        return self._urls[fn]

    def _list_urls(self):
        return self._urls.values()

    # This method contains a body of routines for normalizing the data
    # coming from ESGF
    #     (1) Datasets supply a real number (typically 1e+20) that is to be
    #         interpreted a missing values.  This causes problems with
    #         plotting utilities and interpolation algorithms
    #     (2) The time values differ from dataset to dataset, while the
    #         intervals do not.  With different values, arithmetic on datasets
    #         fails.
    def _clean(self, dataset):
        """Cleans the dataset from ESGF.

        The dataset passed as a parameter is mutable so it gets modified.
        """
        # Replace missing values with numpy's NaN.  The missing value is
        # usually 1e+20, but values can be like 1.0000002e+20, which is
        # different.  Ergo the inequality.
        for var in dataset.data_vars.itervalues():
            if 'missing_value' in var.attrs:
                missing_data_value = var.missing_value
                var.values[var.values >= missing_data_value] = np.NaN

        # FIX ME: This should check if the time type is monClim.  Also, check
        # to see if the first value should be 15.5.  In the meantime, so that
        # the value is at the midpoint of the interval, shift everything by
        # half.
        time0 = dataset.coords['time'][0]
        delta = 0.5*(dataset.coords['time'][1] - dataset.coords['time'][0])
        dataset.coords['time'] -= time0


class LocalDirectoryRepository(NCXRepository):
    """A repository consisting of NC files on the local disk

    This repository is intended primarily for testing and unit tests.
    """
    def __init__(self, repospec):
        self._path = None
        NCXRepository.__init__(self, repospec)

    # The sublass must implement the repository interface.
    def _set_id(self):
        if self._repo_type != 'local':
            msg = ("LocalDirectoryRepository class cannot be created with " +
                   "a specification type {0}.".format(self._repo_type))
            raise TypeError(msg)

        path = self._repo_parameters['path']
        self._path = path
        
        # Use only the directory name for the shortname because it's typed by
        # the user when requesting files.
        id = self._path_leaf(path)
#        self.shortname = sname

        return id

    def _path_leaf(self, path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def _set_authenticator(self):
        auth = NullAuthenticator(self._app)
        return auth

    def _search(self, log, progressbar):
        """Collects the output of ls -1 *nc in the repository directory."""
        self._urls = []
        for filename in os.listdir(self._path):
            url = 'file:////' + filename
            self._urls.append(url)
        self._urls.sort()

    def _push(self, progressbar, ds):
        # The filename comes from the data.
        filename = ds.filename
        filespec = self._path + '/' + filename
        ds.to_netcdf(filespec)
        
    def _retrieve_data(self, log, progressbar, files):

        # Add two to the progress bar.  One for just starting, and another
        # for when it's all finished.  Without these extra, the user can be
        # looking at a blank progress bar for the whole time, since _clean()
        # takes so long.
        temp_ds = []
        file_len = len(files)
        progressbar.start(2*file_len)
        for i, localfile in files:

            # FIX ME: Explore cheaper ways to determine if the file contains
            # the requested variable.  This implementation downloads the
            # entire file, and then discards it.
            xdataset = xr.open_dataset(self._path + '/' + localfile, decode_cf=False)
#            if self._search_params['variable'] in xdataset:

            urlobj = urlparse(localfile)
            filename = urlobj.path.split('/')[-1]
            msg = "Cleaning: [{0}] {1}.".format(urlobj.netloc, filename)
            log.debug(msg)
            progressbar.update(msg)

            # Normalize it.
            # FIX ME: Consider moving this to another place.  This
            # operation is the biggest bottleneck of this searching and
            # retrieving data.
#                self._clean(x)

            temp_ds.append(xdataset)
            msg = "Saved: [{0}] {1}".format(urlobj.netloc, filename)
            log.debug(msg)
            progressbar.update(msg)

        return temp_ds