'''
Created on Dec 22, 2016

@author: neil
'''
import sys
import getpass
from urlparse import urlparse
from plotter import Plotter


def parse_variable_names(var):
    '''
    Some variables don't have original names, and some don't have long names.
    Show a variable name, a long name and the coordinates, choosing
    attributes in this order:
        var name:  original_name, vkey
        long name: long_name, standard_name, vkey
    '''
    if 'long_name' in var.attrs.keys():
        longname = var.attrs['long_name']
    elif 'standard_name' in var.attrs.keys():
        longname = var.attrs['standard_name']
    else:
        longname = var.name

    return {'name': var.name, 'longname': longname}


def parse_params(param_str):
    '''
    Convert a string of the form name='value', ... into a dictionary.  Leading
    and trailing spaces are stripped, as are line-feed, carriage-return, tab,
    single-quote and double-quote characters.
    '''
    params = {}
    for p in param_str.split(','):
        dirty = p.split('=')
        k = dirty[0].strip(' \t\n\r\'\"')
        v = dirty[1].strip(' \t\n\r\'\"')
        params.update({k: v})

    return params

# A text based progress bar.
#
# Thanks to Greenstick (http://stackoverflow.com/users/2206251/greenstick) for
# the printProgress() method.
class ProgressBarText(object):
    
    # The interface object (GUI or console app), which is the frame object,
    # initializes the progress bar.  It is also the frame object that
    # understands the size constraints.  So the size parameters are set
    # here.
    def __init__(self, barLength=50):
        '''Initialize a text based progress bar.  The default length is 50.'''
        self._barLength=barLength
    
    def start(self, counts):
        '''
        Initialize a text base progress bar with a header.
        '''
        self._counts = counts
        self._prefix = 'Progress'
        self._suffix = 'Complete'
        self._i = 0
        
        self._printProgress(0, counts,
                            prefix=self._prefix,
                            suffix=self._suffix,
                            barLength=self._barLength)

    def _printProgress(self, iteration, total,
                       prefix='',
                       suffix='',
                       decimals=1,
                       barLength=100,
                       fill='|'):
        '''
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            barLength   - Optional  : character length of bar (Int)
        '''
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(barLength * iteration // total)
        bar = fill * filledLength + '-' * (barLength - filledLength)
        sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
        if iteration == total:
            sys.stdout.write('\n')
        sys.stdout.flush()

    # FIX ME: Ignore the message for now.
    def update(self, msg):
        self._i += 1
        self._printProgress(self._i, self._counts,
                            prefix=self._prefix,
                            suffix=self._suffix,
                            barLength=self._barLength)

    # No closing operations required for a text-based progress bar.
    def close(self):
        pass

class ConsoleFrame(object):
    
    def __init__(self, app, title):
        self._app = app
        self._title = title

    # The progress bar.  A bar length of 40 works with the Jupyter notebooks.
    # Not using the second parameter in the console.  The progress bar is just
    # a simple text implementation.
    def progressbar(self, dummy):
        return ProgressBarText(barLength=20)

    def get_login_creds(self):
        '''Retrieve a username and password from the command line.'''
        print "Login required"
        username = raw_input('Username: ')
        password = getpass.getpass('Password: ')
        ret = {'username': username, 'password': password}
        return ret
    
    def get_search_params(self):
        print "Enter search parameters like this: variable=ta, institute=NCAR"
        param_string = raw_input('Keyword string: ')
        params = parse_params(param_string)

        return params

    def display_urls(self, urls):
        '''
        List all the URLS found from a search in the given repository.  The
        output is short to accommodate Jupyter notebooks.
        '''
        # FIX ME: Parsing should be done elsewhere.
        for url in urls:
            o = urlparse(url)
            filename = o.path.split('/')[-1]
            print filename
    
    def display_variables(self, datasets):
        '''
        List all the datasets, the variables and coordinates in a tree view.
        '''
        for ds in datasets:
            # FIX ME: Preferably the repository should prepare the list of
            # variables for the tree view.  That's where knowledge about the
            # datasets resides.  The tree view just displays the list, and
            # lets the user select a subset.
            # 
            # For now, build a tuple of the form:
            #    (dataset, variable)
            # and use that as the tag.
            dsline = "Institute: {0}, Model: {1}, Experiment: {2}".format(
                ds.institute_id, ds.model_id, ds.experiment_id)
            print dsline
            
            for vkey in ds.data_vars:
                var = ds[vkey]
                names = parse_variable_names(var)
                varline = " -> {0} ({1}): ".format(names['name'], names['longname'])
                print varline

    def plotdata(self, var, center, time_=0, plev=0):
        if None == center:
            plotter = Plotter()
        else:
            plotter = Plotter(center=center)
        plotter.plotdata(var, time_=time_, plev=plev)

    # Nothing implemented here yet.  A Ncurses terminal interface might be
    # helpful, but that's not trivial to implement.  Short of something like
    # that, the interactive shell is the best.
    def mainloop(self):
        raise NotImplemented("No console based interface implemented." +
                             "  Use the interactive shell and import" +
                             " the class.")

class BasicInterpreterFrame(ConsoleFrame):
    def __init__(self, app, title):
        ConsoleFrame.__init__(self, app, title)
        self._app = app
    
    def mainloop(self):
        import code
        job = self._app
        code.interact(local=locals())