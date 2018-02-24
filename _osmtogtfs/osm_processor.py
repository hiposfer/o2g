"""Utilities for processing OSM data and extracting GTFS relevant transit data."""
import enum
import logging
import hashlib
import osmium as o

from collections import namedtuple, defaultdict
from timezonefinder import TimezoneFinder
from .gtfs_misc import map_osm_route_type_to_gtfs, get_default_route_types


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
    # OSM definitions with their essential attributes
    Node = namedtuple('Node', ['id', 'lon', 'lat', 'tags'])

    class OSMElement(enum.Enum):
        Node = 'n'
        Way = 'w'
        Releation = 'r'

    def __init__(self):
        super(GTFSPreprocessor, self).__init__()
        self.tzfinder = TimezoneFinder()

        # map: node_id -> node
        self.nodes = {}

        # map: way_id -> [locations]
        self.ways = {}

        # map: agency_id -> agency
        self.agencies =\
            {-1: {'agency_id': -1,
                  'agency_url': 'http://hiposfer.com',
                  'agency_name': 'Unknown agency',
                  'agency_timezone': 'Europe/Berlin'}}
        # map of maps: route_type -> map of route_id: route
        self._routes = defaultdict(lambda: {})

        # map: stop_id: stop
        self.stops = {}

        # map to keep track of relation versions (for route types mainly)
        self._relation_versions = {}

        # map to keep track of stops for each route
        self.route_stops = defaultdict(lambda: [])

    @property
    def routes(self):
        """Map of route_id -> route"""
        flat_dict = {}
        for route_type in get_default_route_types():
            if route_type in self._routes:
                flat_dict.update(self._routes[route_type])
        return flat_dict

    def node(self, n):
        """Process each node."""
        try:
            self.nodes[n.id] =\
              GTFSPreprocessor.Node(n.id,
                   n.location.lon,
                   n.location.lat,
                   # Instead of {t.k:t.v for t in n.tags} we only pick the tags that we need,
                   # because this way it is way faster. Try for yourself using cProfile:
                   # python -m cProfile -s cumtime osmtogtfs.py resources/osm/bremen-latest.osm.pbf
                   {'name': n.tags.get('name'), 'public_transport': n.tags.get('public_transport')})
        except o.InvalidLocationError:
            pass

    def way(self, w):
        """Process each way."""
        self.ways[w.id] =\
            [(node.location.lon, node.location.lat) for node in w.nodes]

    def relation(self, rel):
        """Process each relation."""
        if rel.deleted or not rel.visible:
            return

        if rel.tags.get('type') == 'route' and self._is_public_transport(rel.tags.get('route')):
            self.process_route(rel)

    @staticmethod
    def _is_public_transport(route_type):
        """See wether the given route defines a public transport route."""
        return route_type in ['bus', 'trolleybus', 'ferry', 'train', 'tram', 'light_trail']

    def process_route(self, relation):
        """Process one route."""
        # Extract any available transport data
        self.extract_agency(relation)
        self.extract_stops(relation)
        self.extract_routes(relation)

    def extract_agency(self, relation):
        """Extract agency information."""
        # TODO: find out the operator for routes without operator tag.
        # See: http://wiki.openstreetmap.org/wiki/Key:operator
        # Quote from the above link:
        #
        #    If the vast majority of a certain object in an area is operated by a certain
        #    organization and only very few by others then it may be sufficient to only tag the
        #    exceptions. For example, when nearly all roads in an area are managed by a local
        #    authority then it would be sufficient to only tag those that are not with an operator
        #    tag.
        agency_id = self._get_agency_id(relation)
        if agency_id != -1 and agency_id not in self.agencies:
            self.agencies[agency_id] = {'agency_id': agency_id,
                                        'agency_name': relation.tags['operator'],
                                        'agency_timezone': self._guess_timezone(relation)}
        return agency_id

    @staticmethod
    def _get_agency_id(relation):
        """Construct an id for agency using its tags."""
        if 'operator' in relation.tags:
            op_name = relation.tags['operator']
            return int(hashlib.sha256(op_name.encode('utf-8')).hexdigest(), 16) % 10**8
        return -1

    def _guess_timezone(self, relation):
        """Guess timezone of the relation by looking at it's nodes."""
        lon, lat = self._get_first_coordinate(relation)
        timezone = self.tzfinder.timezone_at(lng=lon, lat=lat)
        if not timezone:
            logging.debug('No timezone found for (%s, %s)', lon, lat)
        return timezone

    def _get_first_coordinate(self, relation):
        for member in relation.members:
            if member.ref in self.nodes:
                return self.nodes[member.ref].lon, self.nodes[member.ref].lat
            elif member.ref in self.ways:
                return self._get_first_way_coordinate(member.ref)
        logging.debug('No node found for relation %s', relation.id)
        return 0, 0

    def _get_first_way_coordinate(self, way_id):
        if way_id in self.ways and self.ways[way_id]:
            # Pick the first node
            return self.ways[way_id][0][0], self.ways[way_id][0][1]

    def extract_stops(self, relation):
        """Extract stops in a relation."""
        sequence_id = 0
        for member in relation.members:
            if self._is_stop(member) and self._is_node_loaded(member.ref):
                if member.ref not in self.stops:
                    self.stops[member.ref] = \
                        {'stop_id': member.ref,
                         'stop_name': self.nodes[member.ref].tags.get('name') or\
                            "Unnamed {} stop.".format(relation.tags.get('route')),
                         'stop_lon': self.nodes[member.ref].lon,
                         'stop_lat': self.nodes[member.ref].lat,
                         'route_id': relation.id}
                self.route_stops[relation.id].append(member.ref)
                sequence_id += 1

    def _is_stop(self, member):
        """Check wether the given member designates a public transport stop."""
        return member.role == 'stop' or\
            (member.ref in self.nodes and\
             self.nodes[member.ref].tags.get('public_transport') == 'stop_position')

    def _is_node_loaded(self, node_id):
        """Check whether the node is loaded from the OSM data."""
        return node_id in self.nodes

    def extract_routes(self, relation):
        """Extract information of one route."""
        #if self._is_new_relation(relation):
        if self._is_new_version(relation):
            route_id = relation.id
            route = {'route_id': route_id,
                     'route_short_name': self._create_route_short_name(relation),
                     'route_long_name': self._create_route_long_name(relation),
                     'route_type': map_osm_route_type_to_gtfs(relation.tags.get('route')),
                     'route_url': 'https://www.openstreetmap.org/relation/{}'.format(relation.id),
                     'route_color': relation.tags.get('color'),
                     'agency_id': self._get_agency_id(relation)}
            self._routes[relation.tags.get('route')][route_id] = route
            self._relation_versions[relation.id] = relation.version

    def _is_new_version(self, relation):
        return relation.id not in self._relation_versions or\
            relation.version > self._relation_versions[relation.id]

    @staticmethod
    def _create_route_short_name(relation):
        """Create a meaningful route short name."""
        return relation.tags.get('ref') or ''

    @staticmethod
    def _create_route_long_name(relation):
        """Create a meaningful route name."""
        if relation.tags.get('from') and relation.tags.get('to'):
            return "{0}-to-{1}".format(relation.tags.get('from'),
                                       relation.tags.get('to'))
        name = relation.tags.get('name') or\
               relation.tags.get('alt_name') or\
               "OSM Route No. {}".format(relation.id)
        # Drop route_short_name from this one if it contains it
        route_short_name = GTFSPreprocessor._create_route_short_name(relation)
        if route_short_name and name.startswith(route_short_name):
            # Drop it
            return name[len(route_short_name):]
        return name