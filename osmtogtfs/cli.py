#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import os
import time
import logging
import click

from osmtogtfs.gtfs import gtfs_dummy
from osmtogtfs.gtfs.gtfs_writer import GTFSWriter
from osmtogtfs.osm.exporter import TransitDataExporter


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

    start = time.time()
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

    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        click.echo('GTFS feed saved in %s' % os.path.join(outdir, zipfile))
    else:
        writer.write_unzipped(outdir)
        click.echo('GTFS feed saved in %s' % outdir)

    logging.debug('Done in %d seconds.', (time.time() - start))


if __name__ == '__main__':
    cli()
