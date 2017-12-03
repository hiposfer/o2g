#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import os
import time
import logging

import click

from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter, GTFSRouteType


@click.command()
@click.argument('osmfile', type=click.Path(exists=True, readable=True))
@click.option('--outdir', default='.',
              type=click.Path(exists=True,
                              dir_okay=True,
                              writable=True,
                              resolve_path=True),
              help='Store output in this directory.')
@click.option('--zipfile',
              type=click.Path(file_okay=True,
                              writable=True,
                              resolve_path=True),
              help='Save as Zip file if provided.')
def cli(osmfile, outdir, zipfile):
    processor = GTFSPreprocessor()

    start = time.time()
    processor.apply_file(osmfile, locations=True, idx='sparse_mem_array')
    logging.debug("Preprocessing took %d seconds.", (time.time() - start))

    supported_routes = get_supported_routes(processor)

    writer = GTFSWriter()
    writer.add_agencies(processor.agencies.values())
    writer.add_stops(processor.stops.values())
    writer.add_routes(supported_routes)
    writer.add_shapes(processor.shapes)
    populate_dummy_data(processor, writer, supported_routes)

    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        click.echo('GTFS feed saved in %s' % zipfile)
    else:
        writer.write_unzipped(outdir)
        click.echo('GTFS feed saved in %s' % outdir)


def get_supported_routes(processor):
    route_types = [GTFSRouteType.Bus.value,
                   GTFSRouteType.Tram.value,
                   GTFSRouteType.Subway.value,
                   GTFSRouteType.Rail.value]
    return [route for bulk in processor.routes.values() for version, route in bulk.values()
            if route['route_type'] in route_types]


def populate_dummy_data(processor, writer, routes):
    calendar = create_dummy_calendar()
    trips = create_dummy_trips(routes, calendar)
    writer.add_trips(trips)
    writer.add_stop_times(create_dummy_stoptimes(trips))
    writer.add_calendar(calendar)


def create_dummy_trips(routes, calendar):
    for route in routes:
        for cal in calendar:
            yield {'route_id': route['route_id'],
                   'service_id': cal['service_id'],
                   'trip_id': 'trp_{}'.format(route['route_id']),
                   'shape_id': 'shp_{}'.format(route['route_id'])}


def create_dummy_stoptimes(trips):
    for trip in trips:
        yield {'trip_id': trip['trip_id'],
               'arrival_time': '0:06:10',
               'departure_time': '0:06:10',
               'stop_id': '',
               'stop_sequence': ''}


def create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]


if __name__ == '__main__':
    cli()
