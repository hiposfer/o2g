"""Functionality to build a list of routes."""
import hashlib

from osmtogtfs.osm.models import Route
from osmtogtfs.gtfs.gtfs_misc import map_osm_route_type_to_gtfs


def build_routes(relations):
    for rel in relations.values():
        route = build_route(rel)
        if route:
            yield route


def build_route(relation):
    """Extract information of one route."""
    short_name = create_route_short_name(relation)
    color = relation.tags.get('color')
    return\
        Route(relation.id,
              short_name,
              create_route_long_name(relation, short_name),
              map_osm_route_type_to_gtfs(relation.tags.get('route')),
              'https://www.openstreetmap.org/relation/{}'.format(relation.id),
              color.strip('#') if color else '',
              get_agency_id(relation))


def create_route_short_name(relation):
    """Create a meaningful route short name."""
    return relation.tags.get('ref') or ''


def create_route_long_name(relation, short_name):
    """Create a meaningful route name."""
    if relation.tags.get('from') and relation.tags.get('to'):
        return "{0}-to-{1}".format(relation.tags.get('from'),
                                   relation.tags.get('to'))
    name = relation.tags.get('name') or\
        relation.tags.get('alt_name') or\
        "OSM Route No. {}".format(relation.id)

    # Drop route_short_name from this one if it contains it
    if short_name and name.startswith(short_name):
        # Drop it
        return name[len(short_name):]
    return name


def get_agency_id(relation):
    """Construct an id for agency using its tags."""
    op = relation.tags.get('operator')
    if op:
        return int(hashlib.sha256(op.encode('utf-8')).hexdigest(), 16) % 10**8
    return -1
