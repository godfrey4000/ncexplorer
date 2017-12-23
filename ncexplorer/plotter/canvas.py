'''
Created on May 29, 2017

@author: neil
'''
import matplotlib as mpl

# The Qt5Agg backend, which is what is selected by default, has a bug that
# pegs the CPU at 99%, making the system very slow.  Forcing the backend to
# be TkAgg works around this problem.
mpl.use('TkAgg')
import matplotlib.pyplot as plt

# Turns off the toolbar on the plot window.
mpl.rcParams['toolbar'] = 'None'


class PlottingCanvas(object):
    
    def __init__(self, figsize):
        
        # For newer version, jet isn't the default colormap anymore.
        plt.set_cmap('jet')
        plt.ion()
        self._figure = plt.figure(figsize=figsize)
        self._figsize = figsize
        self._axes = []

    # FIXME:  This is a real kludge.  In jupyter notebooks, the colorbar
    # provokes a IndexException.  This is a temporary work-around until the
    # cause of this can be found and fixed.
    def colorbar_ok(self):
        return True

    def add_map(self):
        # FIXME: Manage the canvas real estate.
        ax = self._figure.add_subplot(111)
        self._axes.append(ax)
        return ax

    def clear(self):
        self._figure.clf()

    def show(self):
        self._figure.show()

    def plotobj(self):
        return plt

    def __unicode__(self):
        pretty = []
        pretty.append("Pyplot instance: %s" % plt)
        pretty.append("Figure instance: %s" % self._figure)
        pretty.append("Number of subplots: %s" % len(self._axes))
        return u'\n'.join(pretty)
    
    def __repr__(self):
        return unicode(self)
    
    def __str__(self):
        return unicode(self).encode('utf-8')


class NotebookCanvas(object):
    
    def __init__(self, figsize):
        self._figure = plt.figure(figsize=figsize)

    def colorbar_ok(self):
        return True

    def add_map(self):
        ax = self._figure.add_subplot(111)
        return ax

    def clear(self):
        pass

    def show(self):
        plt.ion()
