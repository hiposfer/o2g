import osmium as o

from osmtogtfs.osm.models import Way, Point


class WayHandler(o.SimpleHandler):
    def __init__(self, way_ids):
        super(WayHandler, self).__init__()
        self.way_ids = way_ids
        self.ways = {}

    def way(self, w):
        """Process each way."""
        if w.id not in self.way_ids:
            return

        self.ways[w.id] =\
            Way(w.id,
                [Point(n.location.lon, n.location.lat) for n in w.nodes])
