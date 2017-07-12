'''
Created on May 29, 2017

@author: neil
'''
import matplotlib.pyplot as plt


class PlottingCanvas(object):
    
    def __init__(self, figsize):
        self._figure = plt.figure(figsize=figsize)
        self._figsize = figsize
        self._axes = []

    def add_map(self):
        # FIXME: Manage the canvas real estate.
        ax = self._figure.add_subplot(111)
        self._axes.append(ax)
        return ax

    def clear(self):
        self._figure.clf()

    def show(self):
        self._figure.show()

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
