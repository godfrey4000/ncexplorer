'''
Created on Nov 30, 2016

@author: neil
'''

from netCDF4 import Dataset as NetCDFFile

# A place to save all the properties of a dimension as an attribute, once they
# have been parsed.
class NCDimension():
    
    def __init__(self, dim):
        
        self.dataset = dim.group()
        self.dimension = dim
        self.name = None
        self.label = None
        self.size = None
        self.upper_bound = None
        self.lower_bound = None
        self.resolution = None
        
        self._setvals(dim)
    
    def _setvals(self, dim):
        self.name = dim.name
        
        # Write the name to the console log so we know which dimension it
        # barfed on.
        print 'Parsing dimension ' + self.name

        # Some dimensions (e.g. lev in cli_....) do not have a standard name
        # for a nice label.  Fall back on name.
        if hasattr(dim, 'standard_name'):
            self.label = dim.standard_name
        else:
            self.label = dim.name
        self.size = dim.size

        if ('lat' == self.name):
            self.lower_bound = -90
            self.upper_bound = 90
            self.resolution = 30
        if ('lon' == self.name):
            self.lower_bound = -180
            self.upper_bound = 180
            self.resolution = 30
        if (self.name not in ('lat', 'lon')):
            self.lower_bound = 0
            self.upper_bound = dim.size - 1
            self.resolution = 1
                
        
# The NCInterpreter encapsulates all the code dedicated to parsing a NetCDF4
# file.  It can associate dimensions with variables (called coor
class NCInterpreter():

    def __init__(self, ncfile):
        
        self.dataset = NetCDFFile(ncfile)
        self.title = self.dataset.title
        
        # Seems like these NetCDF files have no groups other than the dataset
        # itself.  The variables of the dataset will be the variables that
        # aren't dimensions (coordinates).
        self.variables = {}
        self.dimensions = {}
        for name, var in self.dataset.variables.iteritems():
            
            # Variable name = dimension name means it's a coordinate.
            if name not in self.dataset.dimensions:
                self.variables.update({name: var})
            else:
                # Get the characteristics of the dimensions.
                dim = NCDimension(var)
                self.dimensions.update({name: dim})
    
    def print_info(self):
        print 'Title: ' + getattr(self.dataset, 'title', 'N/A')
        print 'Institution: ' + getattr(self.dataset, 'institution', 'N/A')
        print 'Experiment: ' + getattr(self.dataset, 'experiment', 'N/A')
        print 'Frequency: ' + getattr(self.dataset, 'frequency', 'N/A')
        print 'Realm: ' + getattr(self.dataset, 'modeling_realm', 'N/A')
        print
        print 'Variables:'
        
        for name, var in self.dataset.variables.iteritems():
            try:
                print '[' + name + ']: ' + var.long_name
            except AttributeError:
                print '[' + name + ']: (no long name)'
            except:
                print 'Dimension at time of exception: ' + name
                raise
            
    def list_variables(self):
        retval = self.variables.keys()
        return retval

    def get_dimension(self, dim):
        
        # Just the name is passed in.
        dimobj = self.dimensions[dim]
        return dimobj
        
    def get_variable(self, var, scales):
        
        # Only the name of the variable is given as a parameter.
        varobj = self.dataset.variables[var]
        retdata = varobj
        retval = {}
        for dim in varobj.dimensions:
            
            if (dim not in ('lat', 'lon')):
                val = scales[dim].get()
                retdata = retdata[val]
            
            if ('lat' == dim):
                lat = self.dataset.variables['lat'][:]
                retval.update({'lat': lat})

            if ('lon' == dim):
                lon = self.dataset.variables['lon'][:]
                retval.update({'lon': lon})
        
        retval.update({'data': retdata})
        return retval