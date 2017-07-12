"""
Created on Nov 28, 2016

@author: neil
"""
import sys
import logging
import urllib2
from urlparse import urlparse
from ncexplorer.config import repositories
from repository import NCXESGF, NCXURS, LocalDirectoryRepository
from ncexplorer.util import simple_regrid


def parse_params(param_str):
    """
    Convert a string of the form name='value', ... into a dictionary.  Leading
    and trailing spaces are stripped, as are line-feed, carriage-return, tab,
    single-quote and double-quote characters.
    """
    params = {}
    for param in param_str.split(','):
        dirty = param.split('=')
        key = dirty[0].strip(' \t\n\r\'\"')
        value = dirty[1].strip(' \t\n\r\'\"')
        params.update({key: value})

    return params


# A dictionary like class for storing list data.
class NCDict(dict):
    
    def __init__(self, *args):
        dict.__init__(self, args)
    
    def __repr__(self):
        retstr = ""
        items = self.items()
        for item in items:
            key = item[0]
            value = item[1]
            retstr = retstr + "{0}: {1}\n".format(key, value)
        return retstr
            
    
class FileStore(object):
    """An object in which to save a list of files.
    
    This object is a temporary stub.  It should be replaced by a more robust
    object, perhaps from the collections library.
    
    This is a list of dictionaries of the form [{index, filename}] so that a
    collection of files can be represented like this:
        0: a_file.nc
        1: another_file.nc
    """
    def __init__(self):
        self._store = []
        self._next_i = 0

    def __getitem__(self, index):
        if type(index) is str:
            # FIXME: A collections object can support a more efficient
            # search method.
            for item in self._store:
                if item['filename'] == index:
                    return item['index'], item['filename']
            
            # At this point, the item wasn't found.
            msg = "{} not found.".format(index)
            raise IndexError(msg)

        elif type(index) is int:
            item = self._store[index]
            return item['index'], item['filename']
        else:
            msg = "The file request index must be an integer or a filename"
            raise TypeError(msg)
 
    def __len__(self):
        return len(self._store)

    def append(self, filename):
        entry = {'index': self._next_i, 'filename': filename}
        self._store.append(entry)
        self._next_i += 1

    def pretty_list(self):
        pretty_list = []
        for item in self._store:
            msgline = "{0}: {1}".format(item['index'], item['filename'])
            pretty_list.append(msgline)
        return pretty_list

    def __unicode__(self):
        pretty_list = self.pretty_list()
        return u'\n'.join(pretty_list)
    
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        pretty_list = self.pretty_list()
        return u'\n'.join(pretty_list)

class MatchStore(object):
    """An object in which to store the matches of a search."""
    def __init__(self):
#        self._store = []
        self._store = {}
#        self._next_i = 0

    def __getitem__(self, index):
        # FIXME:  Use ordered dictionary.
        ks = list(self._store)
        key = ks[index]
#        item = self._store[index]
        item = self._store[key]
        return item['index'], item['repository'], item['files']

    def __len__(self):
        return len(self._store)

    def clear(self):
#        self._store = []
        self._store = {}
#        self._next_i = 0
#        self._next_j = 0

    def new_repo(self, repo):
        """Return the repo or create a new one if it doesn't exist."""
        if repo.id in self._store.keys():
            return repo.id

        files = FileStore()
#        entry = {'index': self._next_i, 'repository': repo, 'files': files}
        entry = {'index': repo.id, 'repository': repo, 'files': files}
#        self._store.append(entry)
        self._store[repo.id] = entry
#        self._next_i += 1
        return entry['index']

    def add_file(self, index, filename):
        repo = self._store[index]
        repofiles = repo['files']
        repofiles.append(filename)

    def select(self, selections):
        """Marks entries in the store for download.
        
        The input parameter selections takes the form [(i,j),...].  The second
        entry may be an integer, interpreted as the index.  Or the second entry
        may be a string, interpreted as the filename. 
        """
        # TODO: This can be made more efficient.
        self._selections = MatchStore()
        for repo_index, file_index in selections:
            
            # The first entry must be a string.  Raise a helpful exception if
            # this is not the case.
            if type(repo_index) is not str:
                msg = ("First enrty of a match request must be a string " +
                       "giving the repository's short name.")
                raise TypeError(msg)
                
            item = self._store[repo_index]
            repo = item['repository']
            files = item['files']
            i, filename = files[file_index]
            handle = self._selections.new_repo(repo)
            self._selections.add_file(handle, filename)

        # To avoid calling the getter selections() immediately after making
        # the selections, it can be returned here.
        return self._selections

    def selections(self):
        return self._selections

    def __str__(self):
        pretty_list = []
        for item in self._store:
            msgline = "{0}: {1}".format(item['item'], item['repository'])
            pretty_list.append(msgline)
            fstore = item['files']
            msgsubline = fstore.repr()
            pretty_list.append(msgsubline)
        return u'\n'.join(pretty_list)

# The master application
class Application(object):
    """
    The base application class.
    """
    def __init__(self, frameobj, title):
        self.title = title

#        # The logger.  Each subclass is responsible for the handler.
        self._logger = logging.getLogger(self.title)
        self._logger.setLevel(logging.INFO)
        self._add_log_handler(self._logger)
        self._logger.info(self.title + " starting.")

        # Let the subclass choose the platform for interacting with the user
        # (i.e., GUI or console).  The frame also instantiates a logger for
        # log like updates.
#        self._init_frame(self.title)
        self._frame = frameobj

        # Repositories can be servers that support OpenDAP, or local
        # directories of NetCDF files.
        # TODO: Check runtime if ESGF is supported, and expect that there
        # may be more than one server 
        self.repositories = {}
        for repospec in repositories:
            if repospec['type'] == 'esgf':
                repo = NCXESGF(repospec)
                self._add_repository(repo)
            elif repospec['type'] == 'urs':
                repo = NCXURS(repospec)
                self._add_repository(repo)
            elif repospec['type'] == 'local':
                repo = LocalDirectoryRepository(repospec)
                self._add_repository(repo)
            else:
                msg = ("Encountered unrecognized repository type {0} when " +
                       "adding repositories.".format(repospec['type']))
                self._logger.error(msg)

        # FIX ME: Still not sure about this.  These will probably be
        # references to OpenDAP resources, but not the data stored in memory.
        # A collection of datasets can be very large (~100s of Gb).
        #
        # However, because regridding (FIX ME:  Need reference to more
        # detail on this subject) can take many hours to accomplish, the
        # application will need to be able to save this work.
        self.datasets = {}

        # The variables.
        self.variables = {}
        
        # The repositories and datafile that meet the criteria of a search
        # are stored here.
        self._search_matches = MatchStore()

    # This method must be overriden by the subclass.
    def _add_log_handler(self, log):
        pass

#    # In some instances, e.g., the flask server, the frame needs to be known
#    # to another application.
#    def frame(self):
#        return self._frame

    # Only repository supported is ESGF.
    def _add_repository(self, repo):
        """Add the repository to the dictionary of repositories."""
        # The repository needs to be able to call this objects methods.
        # Setting the app property of the repository will "steal" the
        # repository, meaning if the repository's app property is something
        # else, this call will overwrite it.
        repo.set_app(self)
        self.repositories[repo.id] = repo

    def list_usernames(self):
        """Returns a list of the usernames associated with the repositories."""
        usernames = NCDict()
        for repo_id, repo in self.repositories.iteritems():
            usernames[repo_id] = repo.username()
#            usernames.append({repo_id: repo.username()})
        return usernames

    # FIXME:  This is hardcoded to /home/neil/workspace/data/neil
    def save(self, request):
        """Saves a file to repository.
        
        Accepts a list of tuples of the form (repo, file).  Then calls the
        corresponding repo's save() method with file."""
        for repo_id, ds in request:
            repo = self.repositories[repo_id]
            progressbar = self._frame.progressbar('push')
            repo.push(progressbar, ds)

    # FIX ME: This method would be more robust, and easier to test if it did
    # not presume the existence of a progress bar.  Better if it could work
    # (and return) without a progress bar.
    def search(self, **kwargs):
        """Perform a search for matching NetCDF files.

        Accepts a search string and then searches all supported repositories
        for files that match the parameters of the search string.  The search
        string may be of the form::

            searchstr="experiment='lgm', variable='ta'"

        where the single (or double quotes) surrounding the parameter's value
        are optional.  The search parameters may also be a comma-separated
        list of keyword arguments::

            experiment='lgm', variable='ta'

        The only parameter that is required is ``variable``.
        """
        # In some cases, unit testing most notably, there might not be a
        # progress bar.
        try:
            progressbar = self._frame.progressbar('search')
        except NameError:
            progressbar = None
            self._logger.info("Performing a search without a progress bar.")

        if 'searchstr' in kwargs:
            if len(kwargs['searchstr']) > 0:
                params = parse_params(kwargs['searchstr'])
            else:
                params = {}
        else:
            params = kwargs

        # TODO: If the kwargs is not of the first type, the second type is
        # naively presumed.  This is weak.
        if len(self.repositories) == 0:
            msg = ("Repositories must be added before a search can be performed.")
            raise RuntimeError(msg)

        # If no search parameters are provided, then ask the frame to prompt
        # the user for them.
        if len(params) == 0:
            searchstr = self._frame.get_search_params()
            if len(searchstr) > 0:
                params = parse_params(searchstr)
            else:
                params = {}

#        # A variable must be passed.
#        if 'variable' not in params:
#            msg = "'variable' not included in search parameters."
#            raise RuntimeError(msg)

        # FIX ME: Make the repositories list an object that can return
        # different iterators depending on whether local_only is true or
        # false.
        for repo in self.repositories.values():
            repo.set_search_params(**params)
            
            # Sometimes a server is down.  Therefore catch the URLerror.
            try:
                repo.search(self._logger, progressbar=progressbar)
            except urllib2.URLError, e:
                print e

        if progressbar is not None:
            progressbar.close()

    def search_results(self):
        """Return the results of a search as a list URLs"""
        self._search_matches.clear()
        for repo in self.repositories.values():
            handle = self._search_matches.new_repo(repo)
            for url in repo.urls():
                try:
                    urlobj = urlparse(url)
                except StandardError:
                    if url is None:
                        msg = ("Repository {0} returned None for urls()."
                               ).format(handle)
                    else:
                        msg = ("Could not parse {0} from repository {1}."
                               ).format(url, handle)
                    print msg
                filename = urlobj.path.split('/')[-1]
                self._search_matches.add_file(handle, filename)
        return self._search_matches

    def bind_data(self, request):
        """Creates xarray dataset objects from the request.

        Cycles through the repositories, downloading the selected files, and
        call the frame's display_variables method to display to the user the
        variables contained in the files.
        
        Parameters
        ----------
        request : list of tuples
            The first entry in the tuple is the repository index, which is
            displayed in the output of the application's search() method.  This
            is a string, corresponding to the short name of the repository.
            The second entry in the tuple can be the integer index of the
            specific file or the filename.  Both of these are listed in the
            application's search() method.
        """
        # This can take a while, especially since it depends on external
        # servers and the internet.
        progressbar = self._frame.progressbar('vars')

        ds_index = 0
#        for repo in self.repositories.itervalues():
        selections = self._search_matches.select(request)
        for i, repo, files in selections:

            # Retrieving the data depends on the success of making an HTTP
            # connection, logging on, and completing the conversation with the
            # server.  When it fails, the reason it fails should be displayed
            # to the user as a property of the server (repository?).
            skipds = False
            try:
                datasets = repo.retrieve_data(self._logger, progressbar, files)
            except IOError as err:
                if self._error_is_openid(err):
                    self._logger.error(
                        "OpenID error:  Access failure on node {0}.".format(repo.id)
                    )
                else:
                    self._logger.error("IO error: {0}".format(err))
                skipds = True

            # FIX ME: The error needs to be somehow pushed to the user
            # interface.
            if not skipds:
                
                # The variable datasets can be a list or a generator.  Assume
                # it's a list if it's not a function.
                if callable(datasets):
                    self.datasets[ds_index] = datasets
                else:
                    for i in datasets:
                        self.datasets[ds_index] = i
                        ds_index += 1

        if len(self.datasets) > 0:
            self._frame.display_variables(self.datasets)
        progressbar.close()

    def variable(self, varindex):
        """
        Returns the variable from the application's collection of datasets
        specified by the index.
        """
        # The varindex is a string of this form: i:vname.  The left of the ':'
        # is the index in datasets dictionary, and vname is the variable name
        # as it's represented in the dataset.
        var_selection = varindex.split(':')
        index = int(var_selection[0])
        var = var_selection[1]

        # The Xarray.dataset attribute data_vars gives a dictionary object of
        # the variables.  The attribute variables does not.
        dataset = self.datasets[index]
        retvar = dataset.data_vars[var]
        return retvar

    # FIX ME: Find a better solution for authentication than making the
    # application rely on handling the password.  Someone with access to this
    # code will have access to the password.
    def set_login_creds(self):
        creds = self._frame.get_login_creds()
        return creds

    # The mainloop is trivial, or not implemented in all cases but a desktop
    # application.
    def run(self):
        """The main loop.
        
        Calls the frame's mainloop method."""
        self._frame.mainloop()

    # Periodically, files can't be down loaded because in the client gets
    # redirected to a server that doesn't recognize the OpenID contect.  The
    # server serves a page explaining the a login is required instead of the
    # requested file.  The client process this as if it were a NetCDF file
    # and the parser fails.
    def _error_is_openid(self, err):
        """Checks if the file retrieve failed due to an OpenID failure."""
        if "Access failure" in err.message:
            return True
        else:
            return False

    # Utility Functions.
    # This first method should be a method of the xarray object.
    def regrid(self, var, likevar=None):
        # This can take a while, especially if there is a lot of time data.
        progressbar = self._frame.progressbar('vars')
        newvar = simple_regrid(var, progressbar, likevar)
        return newvar


# The only purpose for a subclass of the Application class is to implement
# different logging functionality.
#
# A command-line application, for driving the application from a command line.
# This class is the intended target for Jupyter Notebooks, development and
# writing automation scripts.
class CmdApplication(Application):
    """An application suitable to the command line.

    This application class is convenient for development and testing.  It is
    also the intended application class for Jupyter Notebooks and bash-based
    automation scripts.
    """
#    def _init_frame(self, title):
#        frame = ConsoleFrame(self, title)
#        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)


class GUIApplication(Application):
    """An application suitable to a desktop GUI.

    This application class is the intended application companion to a GUI that
    is compiled and runs on the local desktop.
    """
#    def _init_frame(self, title):
#        frame = TkinterFrame(self, title)
#        self._frame = frame

    def _add_log_handler(self, log):
        hdlr = logging.StreamHandler(sys.stdout)
        log.addHandler(hdlr)
