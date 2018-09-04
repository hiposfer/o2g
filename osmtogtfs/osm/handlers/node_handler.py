import logging

import osmium as o

from osmtogtfs.osm.models import Node


class NodeHandler(o.SimpleHandler):
    def __init__(self, node_ids):
        super(NodeHandler, self).__init__()
        self.node_ids = node_ids
        self.nodes = {}

    @property
    def missing_node_ids(self):
        """Get a list of nodes not found in OSM data."""
        present_node_ids = self.nodes.keys()
        for nid in self.node_ids:
            if nid not in present_node_ids:
                yield nid

    def node(self, n):
        """Process each node."""
        if n.id not in self.node_ids:
            return

        try:
            self.nodes[n.id] =\
              Node(n.id,
                   n.location.lon,
                   n.location.lat,
                   # Instead of {t.k:t.v for t in n.tags} we only pick the tags that we need,
                   # because this way it is way faster. Try for yourself using cProfile:
                   # python -m cProfile -s cumtime osmtogtfs.py resources/osm/bremen-latest.osm.pbf
                   {'name': n.tags.get('name'), 'public_transport': n.tags.get('public_transport')})
        except o.InvalidLocationError:
            logging.debug('InvalidLocationError at node %s', n.id)
