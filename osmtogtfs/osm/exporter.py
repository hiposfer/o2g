import logging

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

        logging.debug('Found %d public transport relations.', len(self.rh.relations))

        # Collect ids of interest
        node_ids, stop_node_ids, way_ids, reverse_map = self.__collect_ids()

        # Extract nodes
        self.nh = NodeHandler(node_ids)
        self.nh.apply_file(self.filename, locations=True)

        count = 0
        for idx, missing_node_id in enumerate(self.nh.missing_node_ids):
            count += 1
            logging.warning(
                '[no data] stop node: rel %s ref %s.',
                reverse_map[missing_node_id], missing_node_id)

        if count:
            logging.warning(
                '%d nodes that appear in relations are missing.',
                count)
        else:
            logging.debug('Lucky you! All relation member nodes were found.')

        # Extract ways
        self.wh = WayHandler(way_ids)
        self.wh.apply_file(self.filename, locations=True)

    def __collect_ids(self):
        node_ids = set()
        stop_node_ids = set()
        way_ids = set()
        reverse_map = {}

        for rel in self.rh.relations.values():
            for mtype, ref, role in rel.member_info:
                reverse_map[ref] = rel.id

                if mtype in ['n', 'node']:
                    node_ids.add(ref)
                    if role in ['stop', 'platform']:
                        stop_node_ids.add(ref)

                elif mtype in ['w', 'way']:
                    way_ids.add(ref)

                elif mtype in ['r', 'relation']:
                    logging.warning(
                        '[Rel: %s]: super-relations are not supported yet. ref: %s',
                        rel.id, ref)
                else:
                    logging.warning(
                        '[Rel: %s]: unknown member type %s, ref: %s',
                        rel.id, mtype, ref)

        return node_ids, stop_node_ids, way_ids, reverse_map
