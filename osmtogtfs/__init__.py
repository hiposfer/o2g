"""
Extracts partial GTFS feed from OSM data.

OpenStreeMaps data contain information about bus, tram, train and other public
transport means. This information is not enought for providing a complete
routing service, most importantly because it lacks timing data. However, it
still contains routes, stop positions and some other useful data.
"""

__version__ = "0.4.0"
