#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import os
import time
import logging
import click

from _osmtogtfs import gtfs_dummy
from _osmtogtfs.osm_processor import GTFSPreprocessor
from _osmtogtfs.gtfs_writer import GTFSWriter


@click.command()
@click.argument('osmfile', type=click.Path(exists=True, readable=True))
@click.option('--outdir', default='.',
              type=click.Path(exists=True,
                              dir_okay=True,
                              writable=True,
                              resolve_path=True),
              help='Output directory. Default is the current directory.')
@click.option('--zipfile',
              type=click.Path(),
              help='Save to zipfile. Default is saving to flat text files.')
@click.option('--dummy/--no-dummy',
              default=False,
              help='Whether to fill the missing parts with dummy data.')
@click.option('--loglevel',
              default='ERROR',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help="Set the logging level")
def cli(osmfile, outdir, zipfile, dummy, loglevel):
    if loglevel:
        logging.basicConfig(level=loglevel)
    logging.debug('Input: %s', osmfile)
    logging.debug('Output: %s', outdir)
    logging.debug('Zip?: %s', zipfile or False)
    logging.debug('Dummy?: %s', dummy)

    processor = GTFSPreprocessor()
    start = time.time()
    processor.apply_file(osmfile, locations=True, idx='sparse_mem_array')
    logging.debug('Preprocessing took %d seconds.', (time.time() - start))

    writer = GTFSWriter()

    if dummy:
        _populate_dummy_data(writer,
            processor.routes,
            processor.stops,
            processor.route_stops)
        gtfs_dummy.monkey_patch_agencies(processor.agencies)

    writer.add_agencies(processor.agencies.values())
    writer.add_stops(processor.stops.values())
    writer.add_routes(processor.routes.values())

    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        click.echo('GTFS feed saved in %s' % os.path.join(outdir, zipfile))
    else:
        writer.write_unzipped(outdir)
        click.echo('GTFS feed saved in %s' % outdir)

    logging.debug('Done in %d seconds.', (time.time() - start))


def _populate_dummy_data(writer, routes, stops, route_stops):
    dummy = gtfs_dummy.create_dummy_data(routes, stops, route_stops)
    writer.add_trips(dummy.trips)
    writer.add_stop_times(dummy.stop_times)
    writer.add_calendar(dummy.calendar)
    writer.add_shapes(dummy.shapes)


if __name__ == '__main__':
    cli()
