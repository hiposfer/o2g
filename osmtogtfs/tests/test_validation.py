"""osmtogtfs tests."""
import os
import pathlib
import tempfile
import subprocess

import pytest

from osmtogtfs.osm.exporter import TransitDataExporter
from osmtogtfs.gtfs.gtfs_writer import GTFSWriter
from osmtogtfs.gtfs import gtfs_dummy


@pytest.fixture
def transit_data(request):
    root_dir = pathlib.Path(__file__).parents[2]
    filepath = root_dir.joinpath('resources', 'osm', 'freiburg.osm.bz2')
    tde = TransitDataExporter(str(filepath))
    tde.process()
    return tde


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
    w.add_shapes(transit_data.shapes)

    w.add_trips(dummy_transit_data.trips)
    w.add_stop_times(dummy_transit_data.stop_times)
    w.add_calendar(dummy_transit_data.calendar)

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
            ['git', 'clone', '-b', '1.2.16', '--single-branch',
             'https://github.com/google/transitfeed'])

    assert os.path.exists('transitfeed/feedvalidator.py')

    p = subprocess.Popen(['python2.7', 'transitfeed/feedvalidator.py', '-n',
                         dummy_zipfeed],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()

    print("Google Transitfeed's output:\n{}".format(out.decode('utf8')))

    assert 'error' not in out.decode('utf8')
    assert 'errors' not in out.decode('utf8')


def test_shape_id_in_trips(transit_data, dummy_transit_data):
    shape_ids = [shape.shape_id for shape in transit_data.shapes]
    for trip in dummy_transit_data.trips:
        assert trip['shape_id'] in shape_ids
