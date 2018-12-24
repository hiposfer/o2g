"""Functionality to build a list of stops."""
import logging

from o2g.osm.models import Stop


def build_stops(relations, nodes):
    visited_stops_ids = set()
    stop_to_station_map = {}

    # First gsocess all stop_areas
    for rel in relations.values():
        if rel.tags.get('public_transport') != 'stop_area':
            continue

        station = build_parent_stop(rel, nodes)
        if not station:
            continue

        for _, member_id, _ in rel.member_info:
            stop_to_station_map[member_id] = station.stop_id

        visited_stops_ids.add(station.stop_id)
        yield station


    for rel in relations.values():
        if rel.tags.get('public_transport') == 'stop_area':
            continue

        for stop in extract_stops(rel, nodes, visited_stops_ids, stop_to_station_map):
            if stop:
                yield stop


def build_parent_stop(relation, nodes):
    # One stop per stop_area is necessary.
    station_node = None
    some_node = None
    for member_type, member_id, member_role in relation.member_info:
        if member_id not in nodes:
            continue
        some_node = nodes[member_id]
        if not some_node:
            raise Exception()
        if some_node.tags.get('public_transport') == 'station' or \
            some_node.tags.get('amenity') == 'bus_station':
            station_node = some_node

    if not station_node and not some_node:
        logging.debug('No parent node found: https://www.openstreetmap.org/relation/%s' % relation.id)
        return

    if not station_node:
        logging.warn('stop_area without station: https://www.openstreetmap.org/relation/%s' % relation.id)
        logging.warn('Using a random node from the stop_area as reference.')
        station_node = some_node

    return Stop(
        station_node.id,
        station_node.tags.get('name') or "Unnamed stop_area.",
        station_node.lon,
        station_node.lat,
        None,
        _map_wheelchair(station_node.tags.get('wheelchair')),
        1,  # A station in GTFS terms
        '')  # Blank values since stations can't contain other stations.


def extract_stops(relation, nodes, visited_stop_ids, stop_to_station_map):
    """Extract stops in a relation."""
    # member_role: stop, halt, platform, terminal, etc.
    for member_type, member_id, member_role in relation.member_info:

        if member_id not in visited_stop_ids and \
            member_id in nodes and\
                member_role in ('stop', 'halt'):

            location_type = ''

            visited_stop_ids.add(member_id)
            yield Stop(
                member_id,
                nodes[member_id].tags.get('name') or
                "Unnamed {} stop.".format(relation.tags.get('route')),
                nodes[member_id].lon if member_id in nodes else '',
                nodes[member_id].lat if member_id in nodes else '',
                relation.id,
                _map_wheelchair(nodes[member_id].tags.get('wheelchair')),
                location_type,
                stop_to_station_map.get(member_id, ''))


def _map_wheelchair(osm_value):
    if not osm_value:
        return 0
    elif osm_value == 'limited':
        return 1
    elif osm_value == 'yes':
        return 1
    elif osm_value == 'no':
        return 2
    else:
        logging.warn('Unknown OSM wheelchair value %s', osm_value)
        return 0
