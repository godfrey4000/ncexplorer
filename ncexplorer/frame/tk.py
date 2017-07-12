'''
Created on Jan 24, 2017

@author: neil
'''
import Tkinter as tk

# The import of ttk must follow tk, to override the basic tk widgets.
from ttk import Treeview, Button, Entry, Progressbar, Frame, Label

# The Tkinter backend for matplotlib.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#from matplotlib.figure import Figure

#from urlparse import urlparse
#import getpass

from ncexplorer.app import GUIApplication
from ncexplorer.plotter.basemapplotter import TkPlotter
from ncexplorer.frame.base import BaseFrame, BaseProgressBar
#from nc.expframe import parse_params, parse_variable_names


# The coordinates defining the globe's display.
class GlobeCoords(object):
    def __init__(self, center=[0,0], time_=0, plev=0):
        self.center = center
        self.time_ = time_
        self.plev = plev

    def __eq__(self, other):
        '''Equal if each component is equal by value.'''
        if isinstance(other, self.__class__):
            cond1 = (self.center == other.center)
            cond2 = (self.time_ == other.time_)
            cond3 = (self.plev == other.plev) 
            return (cond1 and cond2 and cond3)
        else:
            return NotImplemented

    def __ne__(self, other):
        '''Not equal if any component is different by value.'''
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        else:
            return NotImplemented

    def copy(self, other):
        '''Copy the values of components of the other.'''
        if isinstance(other, self.__class__):
            self.center = other.center
            self.time_ = other.time_
            self.plev = other.plev
            return self
        else:
            return NotImplemented

            
# The GUI is laid out as shown in the diagram.
# +---------------------------------------------------------------+
# |                                 |                             |
# |                                 |                             |
# |                                 |           SEARCH            |
# |                                 |                             |
# |                                 |                             |
# |                                 |                             |
# |           PLOT                  |-----------------------------|
# |                                 |                             |
# |                                 |                             |
# |                                 |           DATA              |
# |                                 |                             |
# |                                 |                             |
# |                                 |                             |
# +---------------------------------------------------------------+
GUI_HEIGHT=600
PLOT_WIDTH=600
CONTROLS_WIDTH=600
SEARCH_HEIGHT=300
VARS_HEIGHT=300

 
class PlotterFrame(Frame):
    '''
    A Tkinter sublcassed frame the provides Tk scale widgets to the Basemap
    plotting canvas to rotate the globe and update the time and plev
    dimensions.
    '''
    def __init__(self, parent):
        Frame.__init__(self, parent)
        
        fleft = Frame(master=self)
        fright = Frame(master=self)
        fleft.pack(side=tk.LEFT)
        fright.pack(side=tk.RIGHT)
        
        frtop = Frame(master=self)
        frmiddle = Frame(master=self)
        frbottom = Frame(master=self)
        frtop.pack()
        frmiddle.pack()
        frbottom.pack()
        
        # Define an object for _plotter, but create the scale widgets first.
        # Protection against the scale objects attempting to update the
        # plotter before it's created.
        self._plotter = None
        
        # The current time, plev and [lat, lon] point specified by the
        # scale widgets.
        self._coordinates = GlobeCoords(center=[30,-120])
        self._globecoords = GlobeCoords(center=[30,-120])

        # There are four scale objects: one each for latitude, longitude,
        # time and plev.
        self._scale_lat = tk.Scale(fleft,
                                label="Latitude",
                                from_=90,
                                to=-90,
                                resolution=30,
                                orient='vertical',
                                length=400,
                                command=self._save)
        self._scale_lon = tk.Scale(frbottom,
                                label="Longitude",
                                from_= -180,
                                to=180,
                                resolution=30,
                                orient='horizontal',
                                length=400,
                                command=self._save)
        self._scale_time = tk.Scale(frtop,
                                    label="Time",
                                    resolution=1,
                                    orient='horizontal',
                                    length=400,
                                    command=self._save)
        self._scale_plev = tk.Scale(frtop,
                                    label="Pressure Level",
                                    resolution=1,
                                    orient='horizontal',
                                    length=400,
                                    command=self._save)
        self._scale_lat.pack()
        self._scale_lon.pack()
        self._scale_time.pack()
        self._scale_plev.pack()
        
        # Set the values of the scales to self._coordindates, otherwise the
        # globe will jump on the first update.
        self._scale_lat.set(self._coordinates.center[0])
        self._scale_lon.set(self._coordinates.center[1])
    
        # The plotter
        self._plotter = TkPlotter(dpi=100,
                                  width=1.0*PLOT_WIDTH/100.0,
                                  height=1.0*GUI_HEIGHT/100.0)
        
        # This draws the empty globe.  It looks better than an empty white
        # square as the application is initializing.
#        self._plotter.clear()
        self._canvas = FigureCanvasTkAgg(self._plotter.figure, frmiddle)
#        self._canvas.show()
        self._canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

#        self._plotter = Plotter(self._axes, center=self._coordinates.center)

        self._poll()

    # Get all four values from the scale widgets and redraw the globe. 
    def _save(self, arg):
        self._coordinates.center = [self._scale_lat.get(), self._scale_lon.get()]
        self._coordinates.time_ = self._scale_time.get()
        self._coordinates.plev = self._scale_plev.get()

    # FIX ME:  The object organization for the plotter has changed.  This
    # is just a patch.  This module needs to be written following the new
    # paradigm.
    def draw(self, time_=0, plev=0, **kwargs):
        self._plotter.draw(time_=0, plev=0, **kwargs)
        
    def _draw(self):
        # The plotter object may not exist.
        if None != self._plotter:
            
            # If we have the variable, then include it.
            try:
                self._plotter.draw(self._axes,
                                   center=self._coordinates.center,
                                   var=self._variable,
                                   time_=self._coordinates.time_,
                                   plev=self._coordinates.plev)

            # Otherwise show the empty globe.
            except AttributeError:
                self._plotter.draw(self._axes,
                                   center=self._coordinates.center)
        
        self._canvas.draw()

    def _poll(self):
        '''Redraws the Basemap globe if any coordinate values have changed.'''
        if self._coordinates != self._globecoords:
            self._draw()
            self._coordinates.copy(self._globecoords)
        self.after(500, self._poll)

    def plotdata(self, var, time_=0, plev=0):
        # The variable var is an xarray variable.
        self._variable = var
        
#        # The time and plev scales need to be adjusted to match the number of
#        # these values in the variable.
#        newto_time = len(var['time'])
#        newto_plev = len(var['plev'])
#        self._scale_time.configure(to=newto_time)
#        self._scale_plev.configure(to=newto_plev)
#        self._draw()
        self._plotter.plotdata(var[0])

class ProgressUpdater(Frame, BaseProgressBar):
    '''
    A Tkinter subclassed widget that presents a progress bar and a message to
    inform the user.
    '''
    def __init__(self, parent, prompt):
        Frame.__init__(self, parent)

        # Calls the parent's update() method.
        self._parent = parent

        # The label is static.  It's just a prompt.  The prompt, the progress
        # bar and the message string are laid out in one row.  E.g.:
        # Prompt: |||||||...........  Updating 1 of 7.
        lbl = Label(self, text=prompt, background='')
        lbl.pack(side=tk.LEFT)

        self._progressbar = Progressbar(self, orient='horizontal')
        self._progressbar.pack(side=tk.LEFT)

        self._message = tk.StringVar()
        msg = Label(self, textvariable=self._message, width=60)
        msg.pack(side=tk.LEFT)

        # FIX ME: Not sure what to do about a default step size.
        self._setsize = 1 

    def update(self, msg=""):
        '''Write the message and advance the progress bar.'''
        self._progressbar.step(self._stepsize)
        self._message.set(msg)
        self._parent.update()

    # This presumes the length is 100, which is the default.
    def start(self, total_steps):
        # The progress bar adds 2 to the total number of steps.  1 is to
        # update the bar at the beginning, before anything is done.  2 is to
        # update the bar at the end.
        self._stepsize = 100.0/(total_steps + 2)
        self.update("")

    # Clearn up.
    def close(self):
        self._setsize = 1
        self.update("")
        self._parent.update()


class SearchFrame(Frame):
    '''
    Create the search cluster of widgets.  The cluster comprises a
    ProgressUpdater widget, a search entry box, a search button to initiate
    the search, and the tree view of URLs that have been found.
    '''
    def __init__(self, parent, handler):
        Frame.__init__(self, parent)

        # The parent's handler for the search button.
        self._parent_handler = handler
        
        # The label and progress bar
        ftop = Frame()
        ftop.pack(anchor=tk.W)
        self.progress_updater = ProgressUpdater(ftop, "Search: ")
        self.progress_updater.pack()

        # The search string and button to launch search.
        fmiddle = Frame()
        fmiddle.pack(anchor=tk.W)
        Button(fmiddle, text="Search", command=self._handler).pack(side=tk.LEFT)
        self._entry = Entry(fmiddle, width=60)
        self._entry.pack(side=tk.LEFT)

        # The tree view lists the source of data found from the search.
        fbottom = Frame()
        fbottom.pack(fill=tk.BOTH, expand=True)
        self._tree = Treeview(fbottom)
        self._tree.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self._tid = self._tree.insert('', index='end', text='Sources')

    def _handler(self):
        search_str = self._entry.get()
        self._parent_handler(search_str)

    def insert(self, dsline):
        self._tree.insert(self._tid, 0, text=dsline)


class VariableFrame(Frame):
    '''right
    Create the variable cluster of widgets.  The cluster comprises a
    ProgressUpdater widget, a retrieve button to retrieve the selected files,
    a tree view of the variables, and a plot button to plot the data.
    '''
    def __init__(self, parent, retriever, plotter):
        Frame.__init__(self, parent)

        # The parent's handlers for retrieving data and plotting the
        # variables.
        self._retriever = retriever
        self._plotter = plotter
        
        # The label and progress bar
        ftop = Frame()
        ftop.pack(anchor=tk.W)
        self.progress_updater = ProgressUpdater(ftop, "Retrieve: ")
        self.progress_updater.pack()

        # The retrieve and plot buttons.
        fbottom = Frame()
        fbottom.pack()
        fbleft = Frame()
        fbleft.pack(side=tk.LEFT, anchor=tk.N)
        Button(fbleft, text="Get Data", command=self._retriever).pack()
        Button(fbleft, text="Plot Data", command=self._plotter).pack()

        # The tree view lists the variables that match the variable supplied
        # in the initial search.
        fbright = Frame()
        fbright.pack(fill=tk.BOTH, expand=True)
        self._tree = Treeview(fbright)
        self._tree.pack(fill=tk.BOTH, expand=True)
        self._tid = self._tree.insert('', index='end', text='Variables')

    def insert(self, dsline, item_id=None, tags=None):
        if None == item_id:
            ret_id = self._tree.insert(self._tid, 0, text=dsline)
        else:
            ret_id = self._tree.insert(item_id, 0, text=dsline, tags=tags)
        return ret_id

    def selection(self):
        item = self._tree.selection()
        ret = self._tree.item(item)
        return ret


class TkinterFrame(BaseFrame):
    '''width=CONTROLS_WIDTH, height=GUI_HEIGHT
    GUI Window made with the Tkinter library.
    '''
    def __init__(self, title):
#        self._app = app
        self._title = title
        self._root = tk.Tk()
        self._root.wm_title(self._title)
        
        # Layout the screen.
        fr_plot = Frame()
        fr_right = Frame()
        fr_plot.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fr_right.pack(side=tk.RIGHT)
        
        fr_rtop = Frame()
        fr_rbottom = Frame()
        fr_rtop.pack(side=tk.TOP)
        fr_rbottom.pack(side=tk.BOTTOM)
        
        self._plotter = PlotterFrame(fr_plot)
        self._plotter.pack()

        # The search area:
#        fr_search = Frame(master=fr_right, width=CONTROLS_WIDTH, height=SEARCH_HEIGHT)
#        fr_search.pack()
        self._fr_search = SearchFrame(fr_rtop, self._search_handler)
        self._fr_search.pack()
        
        # The variables area:
#        fr_vars = Frame(master=fr_right, width=CONTROLS_WIDTH, height=VARS_HEIGHT)
        self._fr_vars = VariableFrame(fr_rbottom, self._get_data, self._plot_handler)
        self._fr_vars.pack()

        # The parent's __init__ still required.
        BaseFrame.__init__(self, title)

    # Methods required to be implemented by the subclass.
    def _set_application(self, title):
        app = GUIApplication(self, title)
        return app

    def _set_progressbar(self):
        ret = self._fr_search.progress_updater
        return ret

    def _set_plotter(self):
        return self._plotter

    def _display_matches(self, matches):
        for i, repo, files in matches:
            dsline = "Repository: {0}".format(repo.id)
            dsid = self._fr_search.insert(dsline)

    def _display_variables(self, payload):
        """List all the datasets in a tree view.
        
        List all the datasets and the variables and coordinates in a tree view.
        """
        i = 0
        for ds in payload:
            dsline = "Institute: {0}, Model: {1}, Experiment: {2}".format(
                ds['Institute'], ds['Model'], ds['Experiment'])
            dsid = self._fr_vars.insert(dsline)
            
            for var in ds['Variables']:
                varline = "  -> {0} ({1}): ".format(
                    var['name'], var['longname'])
                self._fr_vars.insert(varline, item_id=dsid, tags=str(i))

#    # The progress bar and message line.  This is used by the application
#    # while it's searching and retrieving data.
#    def progressbar(self, op):
#        if 'search' == op:
#            ret = self._fr_search.progress_updater
#            return ret
#        if 'vars' == op:
#            ret = self._fr_vars.progress_updater
#            return  ret
#        raise RuntimeError("Expected 'search' or 'vars'.")

#    def progressbar_close(self, hndl):
#        # FIX ME: How to clean this up.
#        pass
#
    def _get_data(self):
        self.bind([(2,1)])

    def _search_handler(self, search_str):
        self.search(searchstr=search_str)
#        params = parse_params(search_str)
#        self._app.search(**params)

    def _plot_handler(self):
        self.plotdata('0:SNOWHICE')
#        item = self._fr_vars.selection()
#        if 'tags' in item:
#            tags = item['tags']
#            name = tags[0]
#            
#            # FIX ME: Can't get get the dataset that is selected, just the
#            # name of the variable.  So for, plotting just the first dataset.
#            ds = self._app.datasets[0]
#            var = ds[name]
#            self._app.plot(var)

#    def display_urls(self, urls):
#        '''
#        List all the URLS found from a search in the given repository.
#        '''
#        # FIX ME: Parsing should be done elsewhere.
#        for url in urls:
#            o = urlparse(url)
#            filename = o.path.split('/')[-1]
#            dsline = "Server: {0}, file: {1}".format(o.netloc, filename)
#            dsid = self._fr_search.insert(dsline)
            
#    def display_variables(self, datasets):
#        '''
#        List all the datasets, the variables and coordinates in a tree view.
#        '''
#        for ds in datasets:
#            # FIX ME: Preferably the repository should prepare the list of
#            # variables for the tree view.  That's where knowledge about the
#            # datasets resides.  The tree view just displays the list, and
#            # lets the user select a subset.
#            # 
#            # For now, build a tuple of the form:
#            #    (dataset, variable)
#            # and use that as the tag.
#            dsline = "Institute: {0}, Model: {1}, Experiment: {2}".format(
#                ds.institute_id, ds.model_id, ds.experiment_id)
#            dsid = self._fr_vars.insert(dsline)
#            
#            for vkey in ds.data_vars:
#                var = ds[vkey]
#                names = parse_variable_names(var)
#                varline = "{0} ({1}): ".format(names['name'], names['longname'])
#                tag = (ds, names['name'])
#                self._fr_vars.insert(varline, item_id=dsid, tags=names['name'])

#    def plotdata(self, var, center, time_=0, plev=0):
#        # Ignore the center.
#        self._plotter.plotdata(var, time_=time_, plev=plev)

#    # Implements the get_login_creds() interface.
#    # FIX ME: This should be a model dialog window.  However, Tkinter does not
#    # have a stock implementation for that.  There are examples of how to
#    # create a model dialog window on the internet, but they all involve
#    # 100 to 200 lines of code code, and none of them work as is. 
#    def get_login_creds(self):
#        '''Retrieve a username and password from the command line.'''
#        print "Login required"
#        username = raw_input('Username: ')
#        password = getpass.getpass('Password: ')
#        ret = {'username': username, 'password': password}
#        return ret

    def mainloop(self):
        self._root.mainloop()
