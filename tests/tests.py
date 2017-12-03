'''osmtogtfs tests.'''
import os
import tempfile
import pytest
import osmium as o

from collections import namedtuple
from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter
from gtfs_misc import GTFSRouteType


# A lightweight data structor to keep preprocessing result for caching
OSMData = namedtuple('OSMData', ['nodes', 'ways', 'agencies', 'stops', 'routes'])


def get_osm_data():
    h = GTFSPreprocessor()
    filepath = os.path.join(os.path.dirname(__file__),
                            os.path.pardir,
                            'resources', 'osm', 'bremen-latest.osm.pbf')
    h.apply_file(filepath,
                 locations=True,
                 idx='sparse_mem_array')
    return OSMData(h.nodes, h.ways, h.agencies, h.stops, h.routes)


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
    w.add_routes(osm.routes.values())
    return w


def test_write_zipped(writer):
    filename = tempfile.mktemp()
    print('Writing GTFS feed to %s' % filename)
    writer.write_zipped(filename)

    assert os.path.exists(filename)
