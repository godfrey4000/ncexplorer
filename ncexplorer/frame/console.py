"""
The console module
------------------

The classes defined in this module provide a command line interface to the
application.  The collection implements the frame interface.

Created on Mar 11, 2017
@author: neil
"""
import sys
from getpass import getpass
from ncexplorer.app import CmdApplication
from ncexplorer.frame.base import BaseFrame, BaseProgressBar
from ncexplorer.plotter.plotter import ScatterPlotter
from ncexplorer.plotter.basemapplotter import BasemapPlotter


# A text based progress bar.
#
# Thanks to Greenstick (http://stackoverflow.com/users/2206251/greenstick) for
# the printProgress() method.
class ProgressBarText(BaseProgressBar):
    
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

    # No closing operations required of a text-based progress bar.
    def close(self):
        pass

class ConsoleFrame(BaseFrame):
    """Does not seem worth it to write these docstrings.  They're not showing
    up in the generated documentation.  The examples I'm seeing all are
    writing the documentation directly into *rst files.
    """
    
    # Methods required to be implemented.
    def _display_matches(self, matches):
        self._matches = matches
        for i, repo, files in matches:
            print "{0}: {1}".format(i, repo.id)
            for j, filename in files:
                print "  {0} - {1}".format(j, filename)
        return matches

    # Choose the CmdApplication for the ConsoleFrame.
    def _set_application(self, title):
        app = CmdApplication(self, title)
        return app

    # The progress bar.  A bar length of 40 works with the Jupyter notebooks.
    # Not using the second parameter in the console.  The progress bar is just
    # a simple text implementation.
    def _set_progressbar(self):
        pb = ProgressBarText(barLength=20)
        return pb

    def _display_variables(self, payload):
        """Print each dataset on a line.
        
        Print each dataset on a line with its variables underneath and
        indented.
        """
        i = 0
        for ds in payload:
            dsline = "{0}: Institute: {1}, Model: {2}, Experiment: {3}".format(
                ds['ID'], ds['Institute'], ds['Model'], ds['Experiment'])
            print dsline

            for var in ds['Variables']:
                varline = "  -> {0} ({1}): ".format(
                    var['name'], var['longname'])
                print varline
            i += 1

    def _plotter(self, **kwargs):
        if 'charttype' in kwargs:
            charttype = kwargs['charttype']
            if charttype.upper() == 'SCATTER':
                plotter = ScatterPlotter()
            elif charttype.upper() == 'MAP':
                plotter = BasemapPlotter(**kwargs)
            else:
                msg = "Unrecognized chart type: {0}.".format(charttype)
                raise RuntimeError(msg)
        else:
            plotter = BasemapPlotter(**kwargs)

        # Let the plotting instance have a reference to this.  The plotting
        # instance needs the figure on the canvas managed by this.
        plotter.set_canvas(self._canvas)
        plotter.set_defaults()
        
        # Launch the canvas window.
        self._canvas.show()
            
        return plotter

    def get_login_creds(self):
        username = raw_input('Username: ')
        password = getpass('Password: ')
        return {'username': username, 'password': password}

    # The console implementation of this presumes that the user specified
    # the intended search parameters at job.search(...).  No need to prompt
    # again.
    def get_search_params(self):
        """Returns empty search string."""
        return ""

    # This is a convenience method for the Console app only.
    def new_plotter(self, **kwargs):
        """Create a new canvas with a single scatter or basemap figure.
        
        This method is only available on the ConsoleFrame."""
        if 'charttype' in kwargs:
            charttype = kwargs['charttype']
            if charttype.upper() == 'SCATTER':
                plotter = ScatterPlotter()
            elif charttype.upper() == 'MAP':
                plotter = BasemapPlotter(**kwargs)
            else:
                msg = "Unrecognized chart type: {0}.".format(charttype)
                raise RuntimeError(msg)
        else:
            plotter = BasemapPlotter(**kwargs)
        
        canvas = self._new_canvas()
        plotter.set_canvas(canvas)
        plotter.set_defaults()
        canvas.show()
        return plotter

    # Nothing implemented here yet.  A Ncurses terminal interface might be
    # helpful, but that's not trivial to implement.  Short of something like
    # that, the interactive shell is the best.
    def mainloop(self):
        """No mainloop implemented.
        
        Later, build an ncurses interface.
        """
        raise NotImplemented("No console based interface implemented. " +
                             " Use the interactive shell and import " +
                             "the class.")
