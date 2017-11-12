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


# def zip_callback(ctx, param, value):
#     if value and ctx.params.get('zipfile') is None:
#         ctx.params['zipfile'] = click.prompt('Zip filename',
#                                 type=click.Path(file_okay=True,
#                                                 writable=True,
#                                                 resolve_path=True))
#     return value

@click.command()
@click.argument('input', type=click.Path(exists=True, readable=True))
@click.option('--outdir', default='.',
              type=click.Path(dir_okay=True,
                              writable=True,
                              resolve_path=True),
              help='Store output in this directory.')
@click.option('--zipfile',
              type=click.Path(file_okay=True,
                              writable=True,
                              resolve_path=True),
              help='Save as Zip file if provided.')
#@click.option('--zip/--no-zip',
#              help='To zip or not to zip the feed.',
#              callback=zip_callback)
def cli(input, outdir, zipfile):
    processor = GTFSPreprocessor()

    start = time.time()
    processor.apply_file(input, locations=True, idx='sparse_mem_array')
    logging.debug("Preprocessing took %d seconds." % (time.time() - start))

    writer = GTFSWriter()
    writer.add_agencies(processor.agencies.values())
    writer.add_stops(processor.stops.values())
    supported_routes = [r for r in processor.all_routes if r['route_type'] in\
        [GTFSRouteType.Bus.value,
         GTFSRouteType.Tram.value,
         GTFSRouteType.Subway.value,
         GTFSRouteType.Rail.value]]
    writer.add_routes(supported_routes)
    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        click.echo('GTFS feed saved in %s' % zipfile)
    else:
        writer.write_unzipped(outdir)
        click.echo('GTFS feed saved in %s' % outdir)


if __name__ == '__main__':
    cli()