'''
Created on Nov 28, 2016

@author: neil
'''
from frame import ConsoleFrame, TkinterFrame
from plotter import plotdata

# The master application
class Application(object):
    '''
    The base application class.
    '''
    def __init__(self, title):
        self.title = title
        
        # Let the subclass choose the platform for interacting with the user
        # (i.e., GUI or console).
        self._init_frame(self.title)
        
        # The respositories are servers that support OpenDAP.  NetCDF files are
        # retrieved from these servers.
        self.repositories = {}
        
        # FIX ME: Still not sure about this.
        self.datasets = []

    # At present, only one repository is supported.  Repositories respond
    # to search requests with datasets.
    def add_repository(self, repo_id, repository):
        '''Add the respository to the dictionary of repositories.'''
        self.repositories.update({repo_id: repository})

    def search(self, **params):
        '''Search the repositories using the kwargs as filters.'''
        if 0 == len(self.repositories):
            raise "Repositories must be added before a search can be performed."

        for repo in self.repositories.values():
            repo.set_search_params(**params)
            self.datasets = repo.bind_data()
            if 0 < len(self.datasets):
                self._frame.display_variables(self.datasets)

    # This plotdata function that this calls is still pretty dumb.
    def plot(self, var):
        plotdata(var)

    # FIX ME;  This is a kludge.
    def plot_nods(self, varname):
        pass

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
    

class GUIApplication(Application):
    '''
    An application suitable to a GUI window.
    '''
    def _init_frame(self, title):
        frame = TkinterFrame(self, title)
        self._frame = frame
