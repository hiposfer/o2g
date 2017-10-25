"""Utilities for processing OSM data and extracting GTFS relevant transit data."""
import enum
from collections import namedtuple

import osmium as o


# OSM definitions with their essential attributes
Node = namedtuple('Node', ['id', 'lon', 'lat', 'tags'])


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
        self.agencies = {}
        self.stops = {}
        self.routes = {}
        self.all_routes = []

    def node(self, n):
        """Process each node."""
        try:
            self.nodes[n.id] = Node(n.id,
                                    n.location.lon,
                                    n.location.lat,
                                    {t.k:t.v for t in n.tags})
        except o.InvalidLocationError:
            pass

    def relation(self, r):
        """Process each relation."""
        if r.tags.get('type') == 'route':
            self.process_route(r)

        if r.tags.get('type') == 'route_master':
            self.process_route_master(r)

    def process_route(self, r):
        """Process one route."""
        if 'public_transport:version' in r.tags and r.tags['public_transport:version'] != 2:
            pass

        agency_id = self.extract_agency(r)

        self.extract_stops(r)

        self.extract_route(r, agency_id)

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
        agency_id = None
        if 'operator' in relation.tags and relation.tags['operator'] not in self.agencies:
            agency_id = id(relation.tags['operator'])
            self.agencies[agency_id] = {'agency_id': agency_id,
                                        'agency_name': relation.tags['operator']}
        return agency_id

    def extract_stops(self, relation):
        """Extract stops in a relation."""
        for m in relation.members:
            if self._is_stop(m):
                if self._is_node_loaded(m.ref) and self.nodes[m.ref].id not in self.stops:
                    self.stops[self.nodes[m.ref].id] = \
                        {'stop_id': self.nodes[m.ref].id,
                         'stop_name': self.nodes[m.ref].tags.get('name'),
                         'stop_lon': self.nodes[m.ref].lon,
                         'stop_lat': self.nodes[m.ref].lat}
                else:
                    print('Route %s requires unavailable node %s' % (relation.id, m.ref))

    def _is_stop(self, member):
        """Check wether the given member designates a public transport stop."""
        return member.role == 'stop' or\
            (member.ref in self.nodes and self.nodes[member.ref].tags.get('public_transport') == 'stop_position')

    def _is_node_loaded(self, node_id):
        """Check whether the node is loaded from the OSM data."""
        return node_id in self.nodes

    def extract_route(self, relation, agency_id):
        """Extract information of one route."""
        if relation.tags.get('route') not in self.routes:
            self.routes[relation.tags.get('route')] = {}

        if relation.id not in self.routes[relation.tags.get('route')] or \
         self.routes[r.tags.get('route')][relation.id][0] < relation.version:
            route = {'route_id': relation.id,
                     'route_short_name': relation.tags.get('name') or relation.tags.get('ref'),
                     'route_long_name': "{0}-to-{1}".format(relation.tags.get('from'),
                                                            relation.tags.get('to')),
                     'route_type': map_osm_route_type_to_gtfs(relation.tags.get('route')),
                     'route_url': 'https://www.openstreetmap.org/relation/{}'.format(relation.id),
                     'route_color': relation.tags.get('color'),
                     'agency_id': agency_id}
            self.routes[relation.tags.get('route')][relation.id] = relation.version, route
            self.all_routes.append(route)
