"""Functionality to build a list of agencies."""
import hashlib

from osmtogtfs.osm.models import Agency


def build_agencies(relations):
    extracted = []
    for rel in relations.values():
        agency = extract_agency(rel)
        if agency and agency.agency_id not in extracted:
            extracted.append(agency.agency_id)
            yield agency


def extract_agency(relation):
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
    if not op:
        return

    agency_id = int(hashlib.sha256(op.encode('utf8')).hexdigest(), 16) % 10**8

    return Agency(agency_id, '', op, '')#self._guess_timezone(relation)}


# def _guess_timezone(self, relation):
#     """Guess timezone of the relation by looking at it's nodes."""
#     lon, lat = self._get_first_coordinate(relation)
#     timezone = self.tzfinder.timezone_at(lng=lon, lat=lat)
#     if not timezone:
#         logging.debug('No timezone found for (%s, %s)', lon, lat)
#     return timezone

# def _get_first_coordinate(self, relation):
#     for member in relation.members:
#         if member.ref in self.nodes:
#             return self.nodes[member.ref].lon, self.nodes[member.ref].lat
#         elif member.ref in self.ways:
#             return self._get_first_way_coordinate(member.ref)
#     logging.debug('No node found for relation %s', relation.id)
#     return 0, 0

# def _get_first_way_coordinate(self, way_id):
#     if way_id in self.ways and self.ways[way_id]:
#         # Pick the first node
#         return self.ways[way_id][0][0], self.ways[way_id][0][1]
