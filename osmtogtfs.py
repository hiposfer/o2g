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
    populate_dummy_data(writer, supported_routes)

    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        click.echo('GTFS feed saved in %s' % zipfile)
    else:
        writer.write_unzipped(outdir)
        click.echo('GTFS feed saved in %s' % outdir)


def get_supported_routes(processor):
    return [r for r in processor.all_routes if r['route_type'] in\
    [GTFSRouteType.Bus.value,
     GTFSRouteType.Tram.value,
     GTFSRouteType.Subway.value,
     GTFSRouteType.Rail.value]]


def populate_dummy_data(writer, supported_routes):
    trips = create_dummy_trips(supported_routes)
    writer.add_trips(trips)
    writer.add_stop_times(create_dummy_stoptimes(trips))
    writer.add_calendar(create_dummy_calendar())


def create_dummy_trips(routes):
  return [{'route_id': '', 'service_id':'', 'trip_id':''}]



def create_dummy_stoptimes(trips):
  return [{'trip_id': '', 'arrival_time': '', 'departure_time': '', 'stop_id': '',
           'stop_sequence':''}]


def create_dummy_calendar():
  return [{'service_id': '', 'monday': '', 'tuesday': '', 'wednesday': '', 'thursday': '',
           'friday': '', 'saturday': '', 'sunday': '', 'start_date': '', 'end_date': ''}]


if __name__ == '__main__':
    cli()


                

