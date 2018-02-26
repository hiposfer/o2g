'''osmtogtfs tests.'''
import os
import tempfile
import subprocess
from collections import namedtuple

import pytest
import osmium as o

from _osmtogtfs.osm_processor import GTFSPreprocessor
from _osmtogtfs.gtfs_writer import GTFSWriter
from _osmtogtfs.gtfs_misc import GTFSRouteType
from _osmtogtfs import gtfs_dummy


# A lightweight data structor to keep preprocessing result for caching
OSMData = namedtuple('OSMData', ['nodes', 'ways', 'agencies', 'stops', 'routes', 'route_stops'])


def get_osm_data():
    h = GTFSPreprocessor()
    filepath = os.path.join(os.path.dirname(__file__),
                            os.path.pardir,
                            'resources', 'osm', 'bremen-latest.osm.pbf')
    h.apply_file(filepath,
                 locations=True,
                 idx='sparse_mem_array')
    return OSMData(h.nodes, h.ways, h.agencies, h.stops, h.routes, h.route_stops)


@pytest.fixture
def transit_data(request):
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
def dummy_transit_data(transit_data):
    return \
        gtfs_dummy.create_dummy_data(transit_data.routes,
            transit_data.stops,
            transit_data.route_stops)


@pytest.fixture
def gtfs_writer(transit_data):
    w = GTFSWriter()

    w.add_agencies(transit_data.agencies.values())
    w.add_stops(transit_data.stops.values())
    w.add_routes(transit_data.routes.values())

    return w


@pytest.fixture
def dummy_gtfs_writer(transit_data, dummy_transit_data):
    w = GTFSWriter()

    # Patch agencies to pass transitfeed check
    for agency in transit_data.agencies.values():
        if 'agency_url' not in agency or not agency['agency_url']:
            agency['agency_url'] = 'http://hiposfer.com'
        if 'agency_timezone' not in agency or not agency['agency_timezone']:
            agency['agency_timezone'] = 'Europe/Berlin'

    w.add_agencies(transit_data.agencies.values())
    w.add_stops(transit_data.stops.values())
    w.add_routes(transit_data.routes.values())

    w.add_trips(dummy_transit_data.trips)
    w.add_stop_times(dummy_transit_data.stop_times)
    w.add_calendar(dummy_transit_data.calendar)
    w.add_shapes(dummy_transit_data.shapes)

    return w


@pytest.fixture
def dummy_zipfeed(dummy_gtfs_writer):
    filename = '{}.zip'.format(tempfile.mktemp())
    print('Writing GTFS feed to %s' % filename)
    dummy_gtfs_writer.write_zipped(filename)

    return filename


def test_write_zipped(gtfs_writer):
    filename = tempfile.mktemp()
    print('Writing GTFS feed to %s' % filename)
    gtfs_writer.write_zipped(filename)

    assert os.path.exists(filename)


def test_duplicate_trips(dummy_transit_data):
    dups = []
    for trip in dummy_transit_data.trips:
        assert trip['trip_id'] not in dups
        dups.append(trip['trip_id'])


def test_validation(dummy_zipfeed):
    """Run transitfeed over the generated feed."""
    # transitfeed is a python2 application. So we need to run it outside
    # python3 process. Moreover, it is not available in pip repostiory.
    # Therefore we have to clone it from git and eventually run it in a
    # process of its own. Finally we parse the standard output and look
    # for errors. We ignore the warnings for now.
    if not os.path.exists('transitfeed'):
        subprocess.check_call(
            ['git', 'clone', '-b', '1.2.16', '--single-branch', 'https://github.com/google/transitfeed'])

    assert os.path.exists('transitfeed/feedvalidator.py')

    p = subprocess.Popen(['python2.7', 'transitfeed/feedvalidator.py', '-n', dummy_zipfeed],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = p.communicate()

    assert 'error' not in out.decode('utf8')
    assert 'errors' not in out.decode('utf8')
