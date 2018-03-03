"""Common types and tools for GTFS processing."""
import enum


class GTFSRouteType(enum.Enum):
    """Route types according to the GTFS specification."""
    Tram = 0
    Subway = 1
    Rail = 2
    Bus = 3
    Ferry = 4
    CableCar = 5
    Gondola = 6
    Funicular = 7


OSM2GTFS_ROUTE_TYPE_MAP = {
    'tram': 0,
    'light_rail': 0,
    'subway': 1,
    'rail': 2,
    'railway': 2,
    'train': 2,
    'bus': 3,
    'ex-bus': 3,
    'ferry': 4,
    'cableCar': 5,
    'gondola': 6,
    'funicular': 7
}


def map_osm_route_type_to_gtfs(route_type, default=-1):
    "Get GTFS equivalent code for the given route type."
    return OSM2GTFS_ROUTE_TYPE_MAP.get(route_type, default)
