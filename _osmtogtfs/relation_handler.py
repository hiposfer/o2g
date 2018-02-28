import osmium as o
import hashlib

from _osmtogtfs.models import Agency, Relation
from _osmtogtfs.gtfs_misc import get_default_route_types


class RelationHandler(o.SimpleHandler):
    def __init__(self):
        super(RelationHandler, self).__init__()
        self.relations = {}
        self.versions = {}

    def relation(self, rel):
        """Process each relation."""
        if any([rel.deleted,
                not rel.visible,
                not self.is_new_version(rel),
                rel.tags.get('type') != 'route']):
            return

        route_tag = rel.tags.get('route')
        if route_tag not in get_default_route_types():
            return

        self.relations[rel.id] = \
            Relation(rel.id, {
                'route': route_tag,
                'operator': rel.tags.get('operator'),
                'color': rel.tags.get('color'),
                'ref': rel.tags.get('ref'),
                'from': rel.tags.get('from'),
                'to': rel.tags.get('to'),
                'alt_name': rel.tags.get('alt_name')},
                [(member.ref, member.role) for member in rel.members])

        self.versions[rel.id] = rel.version


    def is_new_version(self, relation):
        return relation.id not in self.versions or \
            relation.version > self.versions[relation.id]
