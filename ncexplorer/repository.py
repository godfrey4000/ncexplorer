'''
Created on Dec 21, 2016

@author: neil
'''

from pyesgf.logon import LogonManager
from pyesgf.search import SearchConnection
import xarray as xr

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
        
class NCXRepository(object):
    '''
    Base class for searching archives of NetCDF data (repositories),
    retrieving data from the repository, and authenticating to the
    repository if required.
    '''
    def __init__(self, app):
        
        # The search methods will have occasion to ask the application for
        # information, or to perform functions (e.g., logging on to a
        # data source archive.
        #
        # Secondly, the application must know about the repositories.  So the
        # repository must be included in the applications dictionary of
        # repositories.
        self._app = app
        self._app.add_repository(self._repo_id(), self)
        
        # Let the subclass choose the authentication method.
        self._authenticator = self._set_authenticator()

    def attach(self):
        '''
        Create itself as an entry in the dictionary of repsitories in the 
        parent application.
        '''
        self._app.add_repository()  

    def _set_authenticator(self):
        return None
    
    def set_search_params(self, **kwargs):
        self._search_params = kwargs
    
    def bind_data(self):
        '''
        Make the data that matches the search params, available to the
        appliation
        '''
        pass

    def _repo_id(self):
        pass


class NCXESGF(NCXRepository):
    '''
    This class implements the NXSearch interface for ESGF.
    '''
    def bind_data(self):
        '''
        Execute the search using the pyesgf library, which uses the ESGF
        search API.  Then retrieve the data and make it available to the
        application as an xarray dataset object.
        '''
        self._authenticator.login()
        
        # FIX MW: The esgf_node belongs in a configuration file.
        esgf_node = CFG_ESGF_SEARCH_NODE
        conn = SearchConnection(esgf_node, distrib=True)
        ctx = conn.new_context(**self._search_params)
        hit_count = ctx.hit_count

        # Get the file sets
        temp_ds = []
        ds = ctx.search()
        i = 1
        for dsresult in ds:
            # FIX ME: Variable ta is hard-coded.
            files = dsresult.file_context().search(variable='ta')
            print
            print "Searching {0} of {1}.  ({2} files.)".format(i, hit_count, len(files)),
        
            for f in files:
                curfile = f.opendap_url
                x = xr.open_dataset(curfile, decode_cf=False)
                if 'ta' in x:
                    temp_ds.append(x)
                    print
                    print "Found: " + curfile,
                else:
                    print ".",
                
            i = i + 1
        
        # Don't stay logged on.
        self._authenticator.logout()

        # For now, just return the list of datasets.  This should be a single
        # xarray object, agnostic to NetCDF.
        return temp_ds

    def _set_authenticator(self):
        auth = TrivialAuthenticator(self._app)
        return auth

    def _repo_id(self):
        return CFG_ESGF_NODE
