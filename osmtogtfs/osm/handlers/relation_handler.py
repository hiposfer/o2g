import osmium as o

from osmtogtfs.osm.models import Relation


class RelationHandler(o.SimpleHandler):
    def __init__(self):
        super(RelationHandler, self).__init__()
        self.relations = {}
        self.versions = {}

    @property
    def transit_route_types(self):
        """A list of default OSM route types.

        Mainly train and bus types.
        """
        return ['bus', 'ex-bus',        # Bus
                'tram', 'light_rail',   # Tram
                'subway',               # Subway
                'rail', 'railway']      # Rail

    def relation(self, rel):
        """Process each relation."""
        if any([rel.deleted,
                not rel.visible,
                not self.is_new_version(rel),
                rel.tags.get('type') != 'route']):
            return

        route_tag = rel.tags.get('route')
        if route_tag not in self.transit_route_types:
            return

        self.relations[rel.id] = \
            Relation(rel.id, {
                'route': route_tag,
                'operator': rel.tags.get('operator'),
                'color': rel.tags.get('color'),
                'ref': rel.tags.get('ref'),
                'from': rel.tags.get('from'),
                'to': rel.tags.get('to'),
                'name': rel.tags.get('name'),
                'alt_name': rel.tags.get('alt_name'),
                'url': rel.tags.get('url'),
                'contact_website': rel.tags.get('contact:website')},
                [(member.type, member.ref, member.role) for member in rel.members])

        self.versions[rel.id] = rel.version

    def is_new_version(self, relation):
        return relation.id not in self.versions or \
            relation.version > self.versions[relation.id]
