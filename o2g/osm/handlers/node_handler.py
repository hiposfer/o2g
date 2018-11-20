import logging

import osmium as o

from o2g.osm.models import Node


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
                   {t.k: t.v for t in n.tags})
        except o.InvalidLocationError:
            logging.debug('InvalidLocationError at node %s', n.id)
