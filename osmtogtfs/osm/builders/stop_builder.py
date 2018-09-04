"""Functionality to build a list of stops."""
from osmtogtfs.osm.models import Stop


def build_stops(relations, nodes):
    visited_stops_ids = set()
    for rel in relations.values():
        for stop in extract_stops(rel, nodes, visited_stops_ids):
            if stop:
                yield stop


def extract_stops(relation, nodes, visited_stop_ids):
    """Extract stops in a relation."""
    for member_type, member_id, member_role in relation.member_info:

        if member_id not in visited_stop_ids and \
            member_id in nodes and\
                _is_stop(member_id, member_role, nodes):

            visited_stop_ids.add(member_id)
            yield Stop(
                member_id,
                nodes[member_id].tags.get('name') or
                "Unnamed {} stop.".format(relation.tags.get('route')),
                nodes[member_id].lon if member_id in nodes else '',
                nodes[member_id].lat if member_id in nodes else '',
                relation.id)


def _is_stop(member_id, member_role, nodes):
    """Check wether the given member designates a public transport stop."""
    return (member_role in ('stop', 'platform')) or \
        (nodes[member_id].tags.get('public_transport') == 'stop_position')
