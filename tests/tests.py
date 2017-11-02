'''osmtogtfs tests.'''
import os
import tempfile
from collections import namedtuple

import pytest
import osmium as o

from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter, GTFSRouteType


# A lightweight GTFSPreprocessor for test caching
OSMHandler = namedtuple('OSMHandler', ['nodes', 'ways', 'agencies', 'stops', 'routes', 'all_routes'])


@pytest.fixture
def osm(request):
    data = request.config.cache.get('osm_sample', None)
    if not data:
        h = GTFSPreprocessor()
        h.apply_file(os.path.join('tests', 'bremen-latest.osm.pbf'),
                     locations=True,
                     idx='sparse_mem_array')
        data = OSMHandler(h.nodes, h.ways, h.agencies, h.stops, h.routes, h.all_routes)
        request.config.cache.set('osm_sample', data)
    else:
        data = OSMHandler(*data)
    return data


@pytest.fixture
def writer(osm):
    w = GTFSWriter()
    w.add_agencies(osm.agencies.values())
    w.add_stops(osm.stops.values())
    supported_routes = [r for r in osm.all_routes if r['route_type'] in\
        [GTFSRouteType.Bus.value,
         GTFSRouteType.Tram.value,
         GTFSRouteType.Subway.value,
         GTFSRouteType.Rail.value]]
    w.add_routes(supported_routes)
    return w


def test_write_feed(writer):
    filename = tempfile.mktemp()
    print('Writing GTFS feed to %s' % filename)
    writer.write_feed(filename)

    assert os.path.exists(filename)
