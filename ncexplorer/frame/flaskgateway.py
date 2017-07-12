'''
Created on Mar 11, 2017

@author: neil
'''
from ncexplorer.frame.base import BaseFrame
from ncexplorer.plotter import Plotter
import mpld3

class D3Plotter(Plotter):
    '''
    A subclass of Plotter that uses mpld3 to render an HTML version of the
    plot for display in a browser/JS based GUI.
    '''
    def __init__(self, outfn):
        
        self._outfn = outfn

        # The base object uses the default backing, I believe.
        Plotter.__init__(self, figure=True)

    # This function is overriden so that it can push the output to the
    # javascript client.
    def plotdata(self, var, time_=0, plev=0):
        # The parent's draw() method creates the plot.
        try:
            Plotter.draw(self, variable=var, time_=time_, plev=plev)
        except IOError as (errno, strerror):
            msg = "I/O error({0}): {1}".format(errno, strerror)
            self._outfn('error', msg)
            raise
        except:
            msg = "Unexpected error."
            self._outfn('app-error', msg)
            raise
            
        # Then creates and HTML version of the plot and pushes it to the
        # client.
        fightml = self._html()
        self._outfn('plot', {'html': fightml})

    def _html(self):
        fightml = mpld3.fig_to_html(self._figure)
        return fightml

#class DSPlotter(Plotter):
#    def getfig(self):
#        self.get_vars()
#        fig, ax = plt.subplots()
#        plotter = Plotter(axes=ax)
#        plotter.draw(axes=ax, var=self._variable)
#        fightml = mpld3.fig_to_html(fig)
#        return fightml


class DummyProgressbar(object):
    '''A progress bar stub that only holds the data measuring progress.'''
    def __init__(self, outfn):
        self._msg = ""
        self._total_steps = None
        self._step = 0
        self._status = 'not started'

        # The output function.
        self._outfn = outfn

    def update(self, msg=""):
        self._step += 1
        self._msg = msg
        self._send_update()
        
    def start(self, total_steps):
        self._total_steps = total_steps
        self._status = 'in progress'
        
    def close(self):
        self._status = 'completed'
        self._send_update()

    def status(self):
        '''Provides a dictionary with details of the status of a job.'''
        frac = float(self._step)/float(self._total_steps)
        percent = ("{0:." + str(2) + "f}").format(100 * frac)
        ret = {
            'status': self._status,
            'step': self._step,
            'total_steps': self._total_steps,
            'percent': percent,
            'msg': self._msg
        }
        return ret
    
    def _send_update(self):
        data = self.status()
        self._outfn(data)

class FlaskGatewayFrame(BaseFrame):
    
    def __init__(self, title, clientout):

        # Need to override the __init__ to setup the output channel to the
        # javascript client.
        self._clientout = clientout
        
        # The progress bars use the clientout.
        self._search_progress_bar = DummyProgressbar(self._search_out)
        
        # The parent's __init__ still required.
        BaseFrame.__init__(self, title)

    # Output channels.  These are just event/message pairs.
    def _search_out(self, msg):
        self._clientout('pbsearch', msg)

#    def _display_url_out(self, msg):
#        self._clientout('search-result', msg)

    # Methods required to be implemented.
    def _display_matches(self, matches):
        self._clientout('search-result', matches)

    def _set_progressbar(self):
        return self._search_progress_bar

    def _display_variables(self, payload):
        self._clientout('variables', payload)

    def _set_plotter(self):
        plotter = D3Plotter(self._clientout)
        return plotter

    # Nothing implemented here.  The main loop in this case is the web server
    # provided by Flask.
    def mainloop(self):
        raise NotImplemented("No mainloop implemented from the flask " +
                             "gateway.  The flask web server provides " +
                             "this function.")
