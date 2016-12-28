'''
Created on Dec 22, 2016

@author: neil
'''
import code
import getpass
import Tkinter as tk

# The import of ttk must follow tk, to override the basic tk widgets.
from ttk import Treeview, Button, Entry


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


class ConsoleFrame(object):
    
    def __init__(self, app, title):
        self._app = app
        self._title = title
    
    # The main loop for the console app is interactive shell.
    def mainloop(self):
        code.interact(local=locals())

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
        
    def display_variables(self, datasets):
        '''
        List all the datasets, the variables and coordinates on the command line.
        '''
        for ds in datasets:
            print "Institute: {0}, Model: {1}, Experiment: {2}".format(
                ds.institute_id, ds.model_id, ds.experiment_id)
    
            for vkey in ds.keys():
                var = ds[vkey]
                names = parse_variable_names(var)
                    
                print "    {0} ({1}): ".format(
                    names['name'], names['longname']),
                for ckey in var.coords.keys():
                    print "{0}, ".format(ckey),
                print ""


class TkinterFrame(object):
    '''
    GUI Window made with the Tkinter library.
    '''
    def __init__(self, app, title):
        self._app = app
        self._title = title
        self._root = tk.Tk()
        self._root.wm_title(self._title)
        
        # Handler methods are part of this object.  Other objects my not yet
        # exist.
        #
        # The search button:
        b = Button(self._root, text="Search", command=self._search_handler)
        b.pack()
        
        # The plot button:
        pb = Button(self._root, text="Plot", command=self._plot_handler)
        pb.pack()
        
        # The search string.
        self.search_entry = Entry(self._root, width=50)
        self.search_entry.pack()

        # The treeview lists the source of data found from the search.
        self.tree = Treeview(self._root)
        self.tree.pack(fill=tk.BOTH,expand=True)
        self._tid = self.tree.insert('', index='end', text='Sources')

    def _search_handler(self):
        params = self.get_search_params()
        self._app.search(**params)

    def _plot_handler(self):
        item = self.tree.selection()
        item_contents = self.tree.item(item)
        self._app.plot(item)

    def get_search_params(self):
        search_str = self.search_entry.get()
        params = parse_params(search_str)
        return params
        
    def display_variables(self, datasets):
        '''
        List all the datasets, the variables and coordinates in a tree view.
        '''
        for ds in datasets:
            dsline = "Institute: {0}, Model: {1}, Experiment: {2}".format(
                ds.institute_id, ds.model_id, ds.experiment_id)
            dsid = self.tree.insert(self._tid, 0, text=dsline)
            
            for vkey in ds.keys():
                var = ds[vkey]
                names = parse_variable_names(var)
                varline = "{0} ({1}): ".format(
                    names['name'], names['longname'])
                for ckey in var.coords.keys():
                    varline = varline + "{0}, ".format(ckey)
                varid = self.tree.insert(dsid, 0, text=varline, tags=names)

#        self._root.mainloop()
    
    def mainloop(self):
        self._root.mainloop()