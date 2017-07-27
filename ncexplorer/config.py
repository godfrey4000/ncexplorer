'''
Created on Dec 22, 2016

@author: neil
'''
import ConfigParser, os

config = ConfigParser.SafeConfigParser()

# Search these places, in this order for the configuration file.  Seems the
# only way to know that a configuration file was not found is if config.read
# returns and empty list.
config_locations = [
    os.path.expanduser('~/ncexplorer.cfg'),
    os.path.expanduser('~/.ncexplorer.cfg'),
    '/etc/ncexplorer.cfg']
if config.read(config_locations) == []:
    raise IOError(
        "Cannot open configuration file: {0}".format(config_locations))

# ESGF Repository
CFG_ESGF_NODE = config.get('ESGF', 'esgf_node')
CFG_ESGF_SEARCH_NODE = config.get('ESGF', 'esgf_search_node')
CFG_ESGF_OPENID_NODE = config.get('ESGF', 'esgf_openid_node')

# NASA Earthdata Repository
URS_SERVER = config.get('NASA Earthdata', 'urs_server')
URS_DIRECTORY = config.get('NASA Earthdata', 'urs_directory')

# Local repository directories
repodirs = config.items('Directory Repositories')

# Matplotlib backends
MPL_BACKEND_REQUIREMENT = config.get('Matplotlib', 'mpl_backend_requirement')

# Username and password to avoid logging in multiple times.
TRIVIAL_USERNAME = config.get('Authentication', 'username')
TRIVIAL_PASSWORD = config.get('Authentication', 'password')

# Package the repositories up for consumption by the application.
# TODO: Get a dynamic list of repository servers from the config file.
repositories = []
repositories.append({
    'type': 'esgf',
    'parameters': {
        'node': CFG_ESGF_NODE,
        'search_node': CFG_ESGF_SEARCH_NODE,
        'openid_node': CFG_ESGF_OPENID_NODE
        }
    })
repositories.append({
    'type': 'urs',
    'parameters': {
        'server': URS_SERVER,
        'directory': URS_DIRECTORY
        }
    })
for key, path in repodirs:
    repositories.append({
        'type': 'local',
        'parameters': {
            'path': path
            }
        })
