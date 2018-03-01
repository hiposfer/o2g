from osmtogtfs.osm.handlers import RelationHandler, NodeHandler, WayHandler

from osmtogtfs.osm.builders import build_routes, build_stops, build_agencies


class TransitDataExporter(object):
    def __init__(self, filename):
        self.filename = filename
        self.agencies = None
        self.routes = None
        self.stops = None


    def process(self):
        """Process the files and collect necessary data."""

        # Extract relations
        rh = RelationHandler()
        rh.apply_file(self.filename)

        # Collect ids of interest
        ids = {}
        for rel in rh.relations.values():
            for nid, nrole in rel.member_info:
                ids[nid] = None

        # Extract nodes
        nh = NodeHandler(ids)
        nh.apply_file(self.filename, locations=True)

        # Extract ways
        wh = WayHandler(ids)
        wh.apply_file(self.filename, locations=True)

        self.agencies = build_agencies(rh.relations)
        self.routes = build_routes(rh.relations)
        self.stops = build_stops(rh.relations, nh.nodes)
