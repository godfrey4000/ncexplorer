'''
Created on Nov 30, 2016

@author: neil
'''

import Tkinter as tk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.basemap import Basemap


class SliderTK():
    
    def __init__(self, frame, x):
        '''
        A slider object which gives the user the ability to set the value of
        an independent variable.
        '''
        self.frame = frame
        self.label = x.label
        self.lower_bound = x.lower_bound
        self.upper_bound = x.upper_bound
        self.resolution = x.resolution

        self.slider = tk.Scale(
            frame.master,
            orient='horizontal',
            from_=x.lower_bound,
            to=x.upper_bound,
            label=x.label,
            resolution=x.resolution,
            command=self.handle)

    def pack(self):
        '''Position the slider in the frame.'''
        self.slider.pack()

    def vanish(self):
        '''Remove the slider from the frame.'''
        self.pack_forget()
    
    def get(self):
        '''Return the currently selected value.'''
        return self.slider.get()

    # When the slider updates, the frame just needs to be redrawn.  The redraw
    # method interrogates the values of all the sliders.
    def handle(self, val):
        '''Swallow the value passed in and redraw the frame.'''
        self.frame.draw()
        

class CanvasPlotterTK():

    def __init__(self, ncinterpreter):
        
        self.ncinterpreter = ncinterpreter
        self.master = tk.Tk()
        self.master.wm_title(ncinterpreter.title)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)

        # a tk.DrawingArea
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Stuff for managing dimensions.
        self.sliders = {}
        self.variable = None
        self.lons = None
        self.lats = None
        
    def handle_button_click(self):
        whatever = self.variable_list.get()
        self.button_handler(whatever)
    
    def choose_variable(self, callback):
        
        self.button_handler = callback
        options = self.ncinterpreter.list_variables()
        self.variable_list = tk.StringVar(self.master)
        droplist = tk.OptionMenu(self.master, self.variable_list, *options)
        droplist.pack()
        
        button = tk.Button(self.master, text="Update", command=self.handle_button_click)
        button.pack()

    # Add a slider to the canvas to represent values of the independent
    # variable x.
    def add_slider(self, x):
        '''
        Add a slider for controlling the parameter that is passed.  This must
        be an NetCDF dimension.
        '''
        ind_x = self.ncinterpreter.get_dimension(x)
        slider = SliderTK(self, ind_x)
        item = {ind_x.name: slider}
        slider.pack()
        self.sliders.update(item)
        
    def add_variable(self, var):
        
        self.variable = var
        data = self.ncinterpreter.get_variable(var, self.sliders)
        
        # I believe we want to build the grid from the variable's dimensions
        # so that the resolution matches the variable's resolution.
        lat = data['lat']
        lon = data['lon']
        lons, lats = np.meshgrid(lon, lat)
        self.lons = lons
        self.lats = lats
    
    # The value passed by the Scale object will always be passed.  This method
    # swallows it.
    def handle_dimension_event(self, val):
        self.draw()
           
    def draw(self):
        
        # It's possible to get here without a variable, particularly at the
        # beginning.
        if (None == self.variable):
            self.canvas.draw()
            return
        
        if ('lat' in self.sliders.keys()):
            lat = self.sliders['lat'].get()
        else:
            lat = 0
        if ('lon' in self.sliders.keys()):
            lon = self.sliders['lon'].get()
        else:
            lon = 0
        
        # Only the NCInterpreter knows the order of the dimensions in the
        # variable array.
        data = self.ncinterpreter.get_variable(
            self.variable, self.sliders)
        vardata = data['data']
        
#        for key, dim in self.dimensions.iteritems():
#            if ('lat' == key):
#                lat = dim.get()
#            if ('lon' == key):
#                lon = dim.get()

        self.axes.clear()
        self.map = Basemap(ax=self.axes, projection='ortho', lat_0=lat, lon_0=lon)
        self.map.drawcoastlines(linewidth=0.5, color='#444444')
        self.map.fillcontinents(color='#cccccc', alpha=0.5)
        
        # Create the contours of the data.
        x, y = self.map(self.lons, self.lats)
        cs = self.map.contourf(x, y, vardata)

        # This is disabled until I can figure out how to redraw it (rather
        # than overwrite it) each time the map updates.
#        cbar = self.map.colorbar(mappable=cs, fig=self.figure)
        
        self.canvas.draw()

    def mainloop(self):
        tk.mainloop()