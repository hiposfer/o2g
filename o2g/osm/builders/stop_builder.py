"""Functionality to build a list of stops."""
import logging

from o2g.osm.models import Stop


def build_stops(relations, nodes):
    visited_stops_ids = set()
    for rel in relations.values():
        for stop in extract_stops(rel, nodes, visited_stops_ids):
            if stop:
                yield stop


def extract_stops(relation, nodes, visited_stop_ids):
    """Extract stops in a relation."""
    is_stop_area = relation.tags.get('public_transport') == 'stop_area'
    # member_role: stop, platform, terminal, stop_position, etc.
    # stop_area, station, stop_position
    for member_type, member_id, member_role in relation.member_info:

        if member_id not in visited_stop_ids and \
            member_id in nodes and\
                member_role in ('stop', 'platform'):
                #  _is_stop(member_id, member_role, nodes)

            location_type = ''
            parent_station = ''

            visited_stop_ids.add(member_id)
            latest_stop = Stop(
                member_id,
                nodes[member_id].tags.get('name') or
                "Unnamed {} stop.".format(relation.tags.get('route')),
                nodes[member_id].lon if member_id in nodes else '',
                nodes[member_id].lat if member_id in nodes else '',
                relation.id,
                _map_wheelchair(nodes[member_id].tags.get('wheelchair')),
                location_type,
                parent_station)
            yield latest_stop

    # One stop per stop_area is necessary.
    if is_stop_area:
        # For the time being we use the position of the latest
        # stop in the stop_area.
        yield _stop_area(relation, latest_stop)


def _stop_area(relation, latest_stop):
    return Stop(
        relation.id,
        relation.tags.get('name') or
        "Unnamed stop_area.",
        latest_stop.stop_lon,
        latest_stop.stop_lat,
        relation.id,
        0,
        1,  # A station in GTFS terms
        '')  # Blank values since stations can't contain other stations.


def _is_stop(member_id, member_role, nodes):
    """Check wether the given member designates a public transport stop."""
    return (member_role in ('stop', 'platform')) or \
        (nodes[member_id].tags.get('public_transport') == 'stop_position')


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
