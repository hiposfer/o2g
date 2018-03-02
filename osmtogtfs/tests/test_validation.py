"""osmtogtfs tests."""
import os
import pathlib
import tempfile
import subprocess
from collections import namedtuple

import pytest
import osmium as o

from osmtogtfs.osm.exporter import TransitDataExporter
from osmtogtfs.gtfs.gtfs_writer import GTFSWriter
from osmtogtfs.gtfs.gtfs_misc import GTFSRouteType
from osmtogtfs.gtfs import gtfs_dummy


def get_osm_processor():
    root_dir = pathlib.Path(__file__).parents[2]
    filepath = os.path.join(root_dir,
                            'resources', 'osm', 'bremen-latest.osm.pbf')
    tde = TransitDataExporter(filepath)
    tde.process()
    return tde


@pytest.fixture
def transit_data(request):
    # if not hasattr(request.config, 'cache'):
    #     return get_osm_data()

    # data = request.config.cache.get('osm', None)
    # if not data:
    #     data = get_osm_data()
    #     request.config.cache.set('osm', data)
    # else:
    #     data = OSMData(*data)
    return get_osm_processor()


@pytest.fixture
def dummy_transit_data(transit_data):
    return \
        gtfs_dummy.create_dummy_data(transit_data.routes,
            transit_data.stops)


@pytest.fixture
def gtfs_writer(transit_data):
    w = GTFSWriter()

    w.add_agencies(transit_data.agencies)
    w.add_stops(transit_data.stops)
    w.add_routes(transit_data.routes)

    return w


@pytest.fixture
def dummy_gtfs_writer(transit_data, dummy_transit_data):
    w = GTFSWriter()

    # Patch agencies to pass transitfeed check
    patched_agencies = gtfs_dummy.patch_agencies(transit_data.agencies)

    w.add_agencies(patched_agencies)
    w.add_stops(transit_data.stops)
    w.add_routes(transit_data.routes)

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

    print("Google Transitfeed's output:\n{}".format(out.decode('utf8')))

    assert 'error' not in out.decode('utf8')
    assert 'errors' not in out.decode('utf8')


    tde = TransitDataExporter(osmfile)
    tde.process()
    logging.debug('Preprocessing took %d seconds.', (time.time() - start))

    writer = GTFSWriter()
    patched_agencies = None
    if dummy:
        dummy_data = gtfs_dummy.create_dummy_data(list(tde.routes),
                                                  list(tde.stops))
        writer.add_trips(dummy_data.trips)
        writer.add_stop_times(dummy_data.stop_times)
        writer.add_calendar(dummy_data.calendar)
        writer.add_shapes(dummy_data.shapes)
        patched_agencies = gtfs_dummy.patch_agencies(tde.agencies)

    if patched_agencies:
        writer.add_agencies(patched_agencies)
    else:
        writer.add_agencies(tde.agencies)
    writer.add_stops(tde.stops)
    writer.add_routes(tde.routes)
