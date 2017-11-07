'''
Created on Apr 24, 2017

@author: neil
'''
# Locations
# These are centers for orthographic, ... projections.
LOC_JUNEAU = [58.3019, -134.4197]
LOC_MANAUS = [-3.117034, -60.025780]
LOC_UCLA = [34.07, -118.45]

# Continents for Lambert conformal projection.
LAMBERT_NORTH_AMERICA = {
    'standard_lat_S': 45.0,
    'standard_lat_N': 55.0,
    'center_lat': 50.0,
    'center_lon': -107.0,
    'height': 12000000,
    'width': 12000000 }
LAMBERT_SOUTH_AMERICA = {
    'standard_lat_S': -6.0,
    'standard_lat_N': -40.0,
    'center_lat': -23.0,
    'center_lon': -60.0,
    'height': 9000000,
    'width': 9000000 }
LAMBERT_EUROPE = {
    'standard_lat_S': 48.0,
    'standard_lat_N': 60.0,
    'center_lat': 54.0,
    'center_lon': 23.0,
    'height': 6000000,
    'width': 6000000 }
LAMBERT_ASIA = {
    'standard_lat_S': 30.0,
    'standard_lat_N': 60.0,
    'center_lat': 45.0,
    'center_lon': 78.0,
    'height': 11000000,
    'width': 11000000 }
LAMBERT_AFRICA = {
    'standard_lat_S': -12.0,
    'standard_lat_N': 14.0,
    'center_lat': 1.0,
    'center_lon': 21.0,
    'height': 10000000,
    'width': 10000000 }
LAMBERT_AUSTRALIA = {
    'standard_lat_S': -18.0,
    'standard_lat_N': -36.0,
    'center_lat': -27.0,
    'center_lon': 134.0,
    'height': 6000000,
    'width': 6000000 }
LAMBERT_ANTARTICA = {
    'standard_lat_S': -80.0,
    'standard_lat_N': -88.0,
    'center_lat': -84.0,
    'center_lon': 0.0,
    'height': 6000000,
    'width': 6000000 }

#LAMBERT_PACIFIC = {
#    'standard_lat_S': -40.0,
#    'standard_lat_N': 20.0,
#    'center_lat': -9.8,
#    'center_lon': -154.0,
#    'height': 6000000,
#    'width': 6000000 }


# Map colorings.
COLOR_COASTLINES = '#666666'
COLOR_CONTINENTS = '#cccccc'