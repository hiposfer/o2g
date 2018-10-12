"""Functionality to build a list of agencies."""
import hashlib

# from timezonefinder import TimezoneFinder

from osmtogtfs.osm.models import Agency


# TZ_FINDER = TimezoneFinder()


def build_agencies(relations, nodes, ways):
    extracted = []
    for rel in relations.values():
        agency = build_agency(rel, nodes)
        if agency and agency.agency_id not in extracted:
            extracted.append(agency.agency_id)
            yield agency#._replace(agency_timezone=_guess_timezone(rel, nodes, ways))


def build_agency(relation, nodes):
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
    op = relation.tags.get('operator')
    agency_url = relation.tags.get('url') or relation.tags.get('contact_website')

    if not op:
        return

    agency_id = int(hashlib.sha256(op.encode('utf8')).hexdigest(), 16) % 10**8

    return Agency(agency_id, agency_url, op, '')


# def _guess_timezone(relation, nodes, ways):
#     """Guess timezone of the relation by looking at it's nodes."""
#     lon, lat = _get_first_coordinate(relation, nodes, ways)
#     timezone = TZ_FINDER.timezone_at(lng=lon, lat=lat)
#     if not timezone:
#         logging.debug('No timezone found for (%s, %s)', lon, lat)
#     return timezone


# def _get_first_coordinate(relation, nodes, ways):
#     for member_id, member_role in relation.member_info:
#         if member_id in nodes:
#             return nodes[member_id].lon, nodes[member_id].lat
#         elif member_id in ways:
#             return _get_first_way_coordinate(member_id, ways)
#     logging.debug('No node found for relation %s', relation.id)
#     return 0, 0


# def _get_first_way_coordinate(way_id, ways):
#     # Pick the first node
#     return ways[way_id].points[0]
