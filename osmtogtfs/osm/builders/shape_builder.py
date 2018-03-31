"""Functionality to build a list of shapes."""
import logging

from osmtogtfs.osm.models import Shape


def build_shapes(relations, nodes, ways):
    for rel in relations.values():
        route_shape = build_shape(rel, nodes, ways)
        for record in route_shape:
            if record:
                yield record


def build_shape(relation, nodes, ways):
    """Extract shape of one route."""
    sequence_index = 0

    for member_id, _ in relation.member_info:

        shape = None

        if member_id in nodes:
            shape = Shape(
                relation.id,
                nodes[member_id].lat,
                nodes[member_id].lon,
                sequence_index)
            sequence_index += 1

        # Do we need to consider ways too? It dramatically increases the number of shapes.
        # elif member_id in ways:
        #     for point in ways[member_id].points:
        #         shape = Shape(
        #             relation.id,
        #             point.lat,
        #             point.lon,
        #             sequence_index)
        #         sequence_index += 1

        else:
            logging.warning('Relation [%s] member [%s] not available.',
                            relation.id, member_id)

        yield shape
