"""
The frame.base module
---------------------

This module is where the frame interface definition resides.  The interface
consists of designated private methods of the BaseFrame class.  A new user
interface can be implemented by subclassing the BaseFrame class and
implementing these methods.

.. parsed-literal::
   @created: Mar 11, 2017
   @author: neil
"""
from ncexplorer.app import Application
from ncexplorer.repository import NCXESGF
#from ncexplorer.plotter.canvas import PlottingCanvas
from ncexplorer.plotter.canvas import NotebookCanvas


# Extract human understandable names from the variable property of datasets.
def parse_variable_names(var):
    """Parse the variable names.
    
    Some variables don't have original names, and some don't have long names.
    Show a variable name, a long name and the coordinates, choosing
    attributes in this order:

        var name:  original_name, vkey
        long name: long_name, standard_name, vkey
    """
    if 'long_name' in var.attrs.keys():
        longname = var.attrs['long_name']
    elif 'standard_name' in var.attrs.keys():
        longname = var.attrs['standard_name']
    else:
        longname = var.name

    return {'name': var.name, 'longname': longname}


# Since there are many processes that take a while (e.g., searching a
# repository of NetCDF files, downloading them, cleaning and regridding
# data) the full stack makes extensive use of progress bars.  Otherwise,
# the application appears unresponsive.
#
# The presence of this base class establishes the interface the application
# stack requires and a default implementation.
class BaseProgressBar(object):
    """Implements the progress bar interface."""
    def update(self, msg=""):
        """Updates the progress bar."""
        pass
    def start(self, total_steps):
        """Resets the progress bar.
        
        total_steps:  The total number of steps to completion.  Each time the
            method update() is called, the step increases by one.  The percent
            complete is the number of updates()/total_steps.
        """
        pass
    def close(self):
        """This does not do anything."""
        pass

# A dictionary that will give a dataset as an attribute.
# FIXME: Consider subclassing of collections.abc or UserDict
class DatasetDictionary(dict):
    
    @property
    def dataset(self):
        if 'dataset' in self.keys():
            return self['dataset']
    

class BaseFrame(object):
    """The parent class of the family of frame classes.
    
    title:
        The title for the application.  The title is displayed in logs and
        on the window title bar, among other places.
    """
    def __init__(self, title):
        # These methods set the UI objects that the application will call.
        self._progressbar = self._set_progressbar()
        
        # This method sets the application subclass.  The Application object
        # is the main controller -- the heart of the application.
        self._app = self._set_application(title)
        
        # The frame subclass must create the canvas.  The details of the
        # canvas implementation could relate to a web browser, a desktop
        # X window, etc.
        self._canvas = self._new_canvas()

    # These methods constitute the interface.
    def _set_application(self, title):
        """This method must instantiate and return an application instance.
        """
        pass
    def _set_progressbar(self):
        """This method must instantiate and return a progress bar instance.
        """
        pass
    def _plotter(self, **kwargs):
        """FIX ME: this method should instantiate and return an instance of
        a plotting canvas.
        """
        pass
    def _display_matches(self, matches):
        """This method handles displaying the NetCDF files that match a search
        request.
        """
        pass
    def _display_variables(self, payload):
        """This method handles displaying the variables contained in a
        collection of NetCDF files.
        """
        pass
    def get_login_creds(self):
        """This method prompts the user for username and password to be used
        to authenticate to a repository if it is required.
        """
        pass

    def _new_canvas(self):
#        canvas = PlottingCanvas(figsize=(6,6))
        canvas = NotebookCanvas(figsize=(6,6))
        return canvas
        
    def plotter(self, **kwargs):
        """Returns a new instance of the plotter object.
        
        Parameters
        ----------
        plottype : string
            The plottype can either be 'map', or 'scatter'.
        """
        return self._plotter(**kwargs)

    # Useful attributes, particularly when using these objects from the python
    # interpreter.
    # FIX ME: These should python objects instead of console output.
    @property
    def usernames(self):
        """A list of the user names associated with the repositories."""
        return self._app.list_usernames()

    @property
    def variables(self):
        """A list of all the variables known to the application."""
        self.display_variables(self._app.datasets)

    @property
    def datasets(self):
        """A list of the datasets known to the application."""
        retval = []
        for index, ds in self._app.datasets.iteritems():
#            dsdictionary = {}
            dsdictionary = DatasetDictionary()
            dsdictionary['ID'] = index
            dsdictionary['dataset'] = ds
            if not callable(ds):
                if 'institute_id' in ds:
                    dsdictionary['institute'] = ds.institute_id
                if 'institute_id' in ds:
                    dsdictionary['model'] = ds.model_id
                if 'institute_id' in ds:
                    dsdictionary['experiment'] = ds.model_id
            retval.append(dsdictionary)

        return retval 

    # These methods are application methods, exposed here for convenience.
    def variable(self, varspec):
        """Returns a variables.
        
        Takes a specification of the form dataset_index:variable_name and
        returns the xarray DataArray object representing that variable.
        """
        return self._app.variable(varspec)

    def save(self, request):
        """Saves the application's save method."""
        self._app.save(request)

    # This is a higher level workflow.  It accepts a search string from the
    # user and calls the app's search method with it.  The user then presumably
    # selects which of these should be downloaded.  That's done in the bind()
    # method.
    def search(self, **kwargs):
        """Performs a search across all repositories.
        
        This method calls the applications search method.  See the
        application's description for more information.  The application will
        call the display_matches method to let the frame handle displaying
        the results to the user.
        """
        self._app.search(**kwargs)
        matches = self._app.search_results()
        self._display_matches(matches)
        return matches

    def bind(self, matchlist):
        """Builds variables from the selected files.
        
        Takes a subset of the list of URLs that matched the search (matchlist)
        and calls the apps bind() method.  Details of the contents of the files
        and the variables are pushed to the UI.
        
        The matchlist is a list of tuples which have the form (repo, file).
        The file can be either the integer or the filename.
        """        # Enforce type 
        # The app will push the data to the frame in the display_variables()
        # method.  For now, all file are selected.
        self._app.bind_data(matchlist)

    # Methods to support the application object.
    def progressbar(self, dummy):
        """Returns a progress bar."""
        return self._progressbar

#    def get_login_creds(self):
#        '''Retrieve a username and password from the command line.'''
#        print "Login required"
#        username = raw_input('Username: ')
#        password = getpass.getpass('Password: ')
#        ret = {'username': username, 'password': password}
#        return ret
    
    def get_search_params(self):
        """Prompts user for a search parameter string
        
        Returns the search parameter string.
        """
        print "Enter search parameters like this: variable=ta, institute=NCAR"
        param_string = raw_input('Keyword string: ')
        return param_string

#    def display_repo_matches(self):
#        '''
#        List all the URLS found from a search in the given repository.  The
#        output is short to accommodate Jupyter notebooks.
#        '''variables
#        matches = self._app.search_results(filenameonly=True)
#        return self._display_matches(matches)
    
    def display_variables(self, datasets):
        """
        Package all datasets and their properties into a list suitable
        for display in a tree view.  Each dataset itself, contains a set of
        variables which, depending the the capabilities of the frame subclass,
        would be visible when expanding a specified dataset.
        """
        payload = []
        for index, ds in datasets.iteritems():
            # FIX ME: Preferably the repository should prepare the list of
            # variables for the tree view.  That's where knowledge about the
            # datasets resides.  The tree view just displays the list, and
            # lets the user select a subset.
            # 
            # For now, build a tuple of the form:
            #    (dataset, variable)
            # and use that as the tag.
            #
            # The dataset (ds) could be a generator.
            if not callable(ds) and (
                'institute_id' in ds and
                'model_id' in ds and
                'experiment_id' in ds):
                dsdictionary = {
                    'ID': index,
                    'Institute': ds.institute_id,
                    'Model': ds.model_id,
                    'Experiment': ds.experiment_id}
            else:
                dsdictionary = {
                    'ID': index,
                    'Institute': 'unknown',
                    'Model': 'unknown',
                    'Experiment': 'unknown'}
            
            # FIX ME: The determination of the names belongs in the
            # application.
            vars = []
            if callable(ds):
                names = {'name': 'unknown', 'longname': 'unknown'}
                vars.append(names)
            else:
                for vkey in ds.data_vars:
                    var = ds[vkey]
                    names = parse_variable_names(var)
                    vars.append(names)
            dsdictionary['Variables'] = vars

            payload.append(dsdictionary)
        
        # Leave it to the subclass to display the datasets and their variables
        # to the user in the most appropriate way.
        self._display_variables(payload)

    # Utility functions.  These just call the corresponding app method.
    def regrid(self, var, likevar=None):
        return self._app.regrid(var, likevar)

    # This method must be overridden.
    def mainloop(self):
        raise NotImplemented(
            "The mainloop method of the BaseFrame cannot be called " +
            "directly.  Derive a class from BaseFrame and implement " +
            "that mainloop method.")
