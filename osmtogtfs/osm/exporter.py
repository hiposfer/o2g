from osmtogtfs.osm.handlers import RelationHandler, NodeHandler, WayHandler
from osmtogtfs.osm.builders import build_routes, build_stops, build_agencies,\
    build_shapes


class TransitDataExporter(object):
    def __init__(self, filename):
        self.filename = filename
        self.rh = None
        self.nh = None
        self.wh = None

    @property
    def agencies(self):
        return build_agencies(self.rh.relations, self.nh.nodes, self.wh.ways)

    @property
    def routes(self):
        return build_routes(self.rh.relations)

    @property
    def stops(self):
        return build_stops(self.rh.relations, self.nh.nodes)

    @property
    def shapes(self):
        return build_shapes(self.rh.relations, self.nh.nodes, self.wh.ways)

    def process(self):
        """Process the files and collect necessary data."""

        # Extract relations
        self.rh = RelationHandler()
        self.rh.apply_file(self.filename)

        # Collect ids of interest
        ids = {}
        for rel in self.rh.relations.values():
            for nid, _ in rel.member_info:
                ids[nid] = None

        # Extract nodes
        self.nh = NodeHandler(ids)
        self.nh.apply_file(self.filename, locations=True)

        # Extract ways
        self.wh = WayHandler(ids)
        self.wh.apply_file(self.filename, locations=True)
