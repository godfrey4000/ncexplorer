'''
Created on Nov 28, 2016

@author: neil
'''
import sys
import logging
from frame import ConsoleFrame, BasicInterpreterFrame
from frametk import TkinterFrame
from flaskdemo import FlaskJQueryFrame
#from plotter import plotdata
from util import regrid

# The master application
class Application(object):
    '''
    The base application class.
    '''
    def __init__(self, title):
        self.title = title
        
        # Let the subclass choose the platform for interacting with the user
        # (i.e., GUI or console).  The frame also instantiates a logger for
        # log like updates.
        self._init_frame(self.title)
        
        # The repositories are servers that support OpenDAP.  NetCDF files are
        # retrieved from these servers.
        self.repositories = {}
        
        # FIX ME: Still not sure about this.  These will probably be
        # references to OpenDAP resources, but not the data stored in memory.
        # A collection of datasets can be very large (~100s of Gb).
        # 
        # However, because regridding (FIX ME:  Need reference to more
        # detail on this subject) can take many hours to accomplish, the
        # application will need to be able to save this work.
        self.datasets = []
        
        # The logger.  Each subclass is responsible for the handler.
        self._logger = logging.getLogger(self.title)
        self._logger.setLevel(logging.INFO)
        self._add_log_handler(self._logger)

    # At present the only repository supported is ESGF.
    def add_repository(self, repo):
        '''Add the repository to the dictionary of repositories.'''
        # The repository needs to be able to call this objects methods.
        # Setting the app property of the repository will "steal" the
        # repository, meaning if the repository's app property is something
        # else, this call will overwrite it.
        repo.set_app(self)
        self.repositories[repo.id] = repo

    def search(self, **params):
        '''Search the repositories using the kwargs as filters.'''
        if 0 == len(self.repositories):
            errMsg = ("Repositories must be added before" +
                      " a search can be performed.")
            raise RuntimeError(errMsg)

        # If no search parameters are provided, then ask the frame to prompt
        # the user for them.
        if len(params) == 0:
            params = self._frame.get_search_params()

        # A variable must be passed.
        if 'variable' not in params:
            errMsg = ("'variable' not included in search params." +
                      "  All searches must include a variable.")
            raise RuntimeError(errMsg)

        pb = self._frame.progressbar('search')
        for repo in self.repositories.values():
            repo.set_search_params(**params)
            repo.search(self._logger, pb)
        pb.close()
        
        # Let the frame display the results to the users.
        self._frame.display_urls(repo.urls())

    # This actually removes items from the list.
    def select(self):
        pass

    def bind_data(self):
        # This can take a while, especially since it depends on external
        # servers and the internet.
        pb = self._frame.progressbar('vars')
        
        for repo in self.repositories.itervalues():
            self.datasets = repo.retrieve_data(self._logger, pb)

        if 0 < len(self.datasets):
            self._frame.display_variables(self.datasets)
        pb.close()

    def extract_vars(self, variable):
        variables = []
        for ds in self.datasets:
            var = ds[variable]
            variables.append(var)
        return variables

    def regrid(self, variable, lattice='union', tl=None, pl=None):
        # extract the variables from the datasets.
        variables = self.extract_vars(variable)
        new_variables = regrid(variables,
                               lattice=lattice,
                               tl=tl,
                               pl=pl)
        return new_variables
        
    # The center argument is provided because some implementations of the
    # display canvas (e.g. ortho projection) does not show the whole globe
    # and cannot be turned.
    def plot(self, var, center=None, time_=0, plev=0):
        self._frame.plotdata(var, center, time_=time_, plev=plev)

    # FIX ME: Find a better solution for authentication than making the
    # application rely on handling the password.  Someone with access to this
    # code will have access to the password.
    def set_login_creds(self):
        creds = self._frame.get_login_creds()
        return creds
    
    # To start, this is just search, select, plot.
    def run(self):
        '''
        The main loop.
        '''
        self._frame.mainloop()

            
# A command-line application, for driving the application from a command line.
class CmdApplication(Application):
    '''
    An appliction suitable to the command line.  This application class is
    convenient for development and testing.
    '''
    def _init_frame(self, title):
        frame = ConsoleFrame(self, title)
        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)

# Very basic, interpreter.  For debugging.
class BasicInterpreterApplication(Application):
    def _init_frame(self, title):
        frame = BasicInterpreterFrame(self, title)
        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)

class GUIApplication(Application):
    '''
    An application suitable to a GUI window.
    '''
    def _init_frame(self, title):
        frame = TkinterFrame(self, title)
        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)
        
class WebApplication(Application):
    '''
    A web application utilizing a JQuery/Flask stack.
    '''
    def _init_frame(self, title):
        frame = FlaskJQueryFrame(self, title)
        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)
