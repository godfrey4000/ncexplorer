'''
Created on Dec 22, 2016

@author: neil
'''
import ConfigParser, os

config = ConfigParser.ConfigParser()

# FIX ME: Change the default location
default_loc = '/home/neil/workspace/proj-eclipse/ncexplorer/etc/ncexplorer.cfg'
config.read([default_loc, os.path.expanduser('~/.ncexplorer.cfg')])

# ESGF
CFG_ESGF_NODE = config.get('ESGF', 'esgf_node')
CFG_ESGF_SEARCH_NODE = config.get('ESGF', 'esgf_search_node')
CFG_ESGF_OPENID_NODE = config.get('ESGF', 'esgf_openid_node')
