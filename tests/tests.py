'''osmtogtfs tests.'''
import os
import tempfile
from collections import namedtuple

import pytest
import osmium as o

from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter, GTFSRouteType


# A lightweight data structor to keep preprocessing result for caching
OSMData = namedtuple('OSMData', ['nodes', 'ways', 'agencies', 'stops', 'routes', 'all_routes'])


def get_osm_data():
    h = GTFSPreprocessor()
    h.apply_file(os.path.join('..', 'resources', 'osm', 'bremen-latest.osm.pbf'),
                 locations=True,
                 idx='sparse_mem_array')
    return OSMData(h.nodes, h.ways, h.agencies, h.stops, h.routes, h.all_routes)


@pytest.fixture
def osm(request):
    if not hasattr(request.config, 'cache'):
        return get_osm_data()

    data = request.config.cache.get('osm', None)
    if not data:
        data = get_osm_data()
        request.config.cache.set('osm', data)
    else:
        data = OSMData(*data)
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


def test_write_zipped(writer):
    filename = tempfile.mktemp()
    print('Writing GTFS feed to %s' % filename)
    writer.write_zipped(filename)

    assert os.path.exists(filename)
