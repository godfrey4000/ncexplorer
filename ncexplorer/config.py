'''
Created on Dec 22, 2016

@author: neil
'''
import ConfigParser, os
from docutils.parsers.rst.directives import path

config = ConfigParser.ConfigParser()

# FIX ME: Change the default location
default_loc = '/home/neil/workspace/proj-eclipse/ncexplorer/etc/ncexplorer.cfg'
config.read([default_loc, os.path.expanduser('~/.ncexplorer.cfg')])

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
