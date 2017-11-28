"""Utilities for processing OSM data and extracting GTFS relevant transit data."""
import enum
import logging
from collections import namedtuple, defaultdict

import osmium as o
from timezonefinder import TimezoneFinder


# OSM definitions with their essential attributes
Node = namedtuple('Node', ['id', 'lon', 'lat', 'tags'])
Location = namedtuple('Location', ['lon', 'lat'])


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
    "Return numeral code for the given route type."
    return OSM2GTFS_ROUTE_TYPE_MAP.get(route_type, default)


class OSMElement(enum.Enum):
    Node = 'n'
    Way = 'w'
    Releation = 'r'


class GTFSPreprocessor(o.SimpleHandler):
    """Extracts GTFS relevant transit data in order to construct a feed.

    To understand how osmium deals with its OSM objects make sure to read
    the docs at http://docs.osmcode.org/pyosmium/latest/intro.html#reading-osm-data.
    Here is the most important concept from the docs:

        It is important to remember that the object references that are handed
        to the handler are only temporary. They will become invalid as soon as
        the function returns. Handler functions must copy any data that should
        be kept for later use into their own data structures. This also includes
        attributes like tag lists.

    If you don't respect the above, you'll get segmentation faults.
    """

    def __init__(self):
        super(GTFSPreprocessor, self).__init__()

        self.nodes = {}
        self.ways = {}
        self.agencies = {-1: {'agency_id': -1, 'agency_name': 'Unknown agency', 'agency_timezone': ''}}
        self.stops = {}
        self.routes = defaultdict(lambda: {})
        self.all_routes = []
        self.tzfinder = TimezoneFinder()

    def node(self, n):
        """Process each node."""
        try:
            self.nodes[n.id] = Node(n.id,
                                    n.location.lon,
                                    n.location.lat,
                                    {t.k:t.v for t in n.tags})
        except o.InvalidLocationError:
            pass

    def way(self, w):
        """Process each way."""
        # For the moment we only need node locations of each way.
        self.ways[w.id] = [loc for loc in map(self._make_location, w.nodes) if loc]

    def _make_location(self, node):
        try:
            return Location(node.location.lon, node.location.lat)
        except:
            return None

    def relation(self, r):
        """Process each relation."""
        if r.deleted or not r.visible:
            return

        if r.tags.get('type') == 'route' and self._is_public_transport(r.tags.get('route')):
            self.process_route(r)

        if r.tags.get('type') == 'route_master':
            self.process_route_master(r)

    def _is_public_transport(self, route_type):
        """See wether the given route defines a public transport route."""
        return route_type in ['bus', 'trolleybus', 'ferry', 'train', 'tram', 'light_trail']

    def process_route(self, r):
        """Process one route."""

        self.extract_agency(r)

        self.extract_stops(r)

        self.extract_route(r)

        # TODO: Extract trips
        # TODO: Extract trip's shapes
        # TODO: Create and link dummy stop times
        # TODO: Create and link dummy cal_dates or calendar

    def process_route_master(self, r):
        """Process one master route."""
        pass

    def extract_agency(self, relation):
        """Extract agency information."""
        # TODO: find out the operator for routes without operator tag.
        # See: http://wiki.openstreetmap.org/wiki/Key:operator
        # Quote from the above link:
        #
        #    If the vast majority of a certain object in an area is operated by a certain organization
        #    and only very few by others then it may be sufficient to only tag the exceptions.
        #    For example, when nearly all roads in an area are managed by a local authority then it
        #    would be sufficient to only tag those that are not with an operator tag.
        agency_id = self._get_agency_id(relation)
        if agency_id != -1 and agency_id not in self.agencies:
            self.agencies[agency_id] = {'agency_id': agency_id,
                                        'agency_name': relation.tags['operator'],
                                        'agency_timezone': self._guess_timezone(relation)}
        return agency_id

    def _get_agency_id(self, relation):
        """Construct an id for agency using its tags."""
        if 'operator' in relation.tags:
            return relation.tags['operator']
        else:
            return -1

    def _guess_timezone(self, relation):
        """Guess timezone of the relation by looking at it's nodes."""
        lon, lat = self._get_first_coordinate(relation)
        tz = self.tzfinder.timezone_at(lng=lon, lat=lat)
        if not tz:
            logging.debug('No timezone found for (%s, %s)' % (lon, lat))
        return tz

    def _get_first_coordinate(self, relation):
        for m in relation.members:
            if m.ref in self.nodes:
                return self.nodes[m.ref].lon, self.nodes[m.ref].lat
            elif m.ref in self.ways:
                return self._get_first_way_coordinate(m.ref)
        logging.debug('No node found for relation %s' % relation.id)
        return 0, 0

    def _get_first_way_coordinate(self, way_id):
        if len(self.ways[way_id]) > 0:
            # Pick the first node
            return self.ways[way_id][0].lon, self.ways[way_id][0].lat

    def extract_stops(self, relation):
        """Extract stops in a relation."""
        for m in relation.members:
            if m.ref not in self.stops and self._is_stop(m):
                if self._is_node_loaded(m.ref):
                    self.stops[self.nodes[m.ref].id] = \
                        {'stop_id': self.nodes[m.ref].id,
                         'stop_name': self.nodes[m.ref].tags.get('name') or "Unnamed {} stop.".format(relation.tags.get('route')),
                         'stop_lon': self.nodes[m.ref].lon,
                         'stop_lat': self.nodes[m.ref].lat}

    def _is_stop(self, member):
        """Check wether the given member designates a public transport stop."""
        return member.role == 'stop' or\
            (member.ref in self.nodes and self.nodes[member.ref].tags.get('public_transport') == 'stop_position')

    def _is_node_loaded(self, node_id):
        """Check whether the node is loaded from the OSM data."""
        return node_id in self.nodes

    def extract_route(self, relation):
        """Extract information of one route."""
        if relation.id not in self.routes[relation.tags.get('route')] or \
         self.routes[relation.tags.get('route')][relation.id][0] < relation.version:
            route = {'route_id': relation.id,
                     'route_short_name': relation.tags.get('name') or relation.tags.get('ref'),
                     'route_long_name': self._create_route_long_name(relation),
                     'route_type': map_osm_route_type_to_gtfs(relation.tags.get('route')),
                     'route_url': 'https://www.openstreetmap.org/relation/{}'.format(relation.id),
                     'route_color': relation.tags.get('color'),
                     'agency_id': self._get_agency_id(relation)}
            self.routes[relation.tags.get('route')][relation.id] = relation.version, route
            self.all_routes.append(route)

    def _create_route_long_name(self, relation):
        """Create a meaningful route name."""
        if not relation.tags.get('from') or not relation.tags.get('to'):
            return ''
        return "{0}-to-{1}".format(relation.tags.get('from'),
                                   relation.tags.get('to'))
