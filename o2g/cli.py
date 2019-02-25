#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import os
import time
import tempfile
import logging
from logging import FileHandler
from contextlib import contextmanager
from pathlib import Path

import argparse

from o2g import __version__
from o2g.gtfs import gtfs_dummy
from o2g.gtfs.gtfs_writer import GTFSWriter
from o2g.osm.exporter import TransitDataExporter
from o2g.web import dl_osm_from_overpass


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, prospective_dir, option_string=None):
        if not os.path.isdir(prospective_dir):
            parser.print_usage()
            print('Try "{} --help" for help.\n'.format(parser.prog))
            parser.exit("Error: Inavlid path: {0}".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            parser.print_usage()
            print('Try "{} --help" for help.\n'.format(parser.prog))
            parser.exit("Error: Unreadable dir: {0}".format(prospective_dir))


class readable_file(argparse.Action):
    def __call__(self, parser, namespace, prospective_file, option_string=None):
        if not os.path.isfile(prospective_file):
            parser.print_usage()
            print('Try "{} --help" for help.\n'.format(parser.prog))
            parser.exit("Error: Inavlid file: {0}".format(prospective_file))
        if os.access(prospective_file, os.R_OK):
            setattr(namespace, self.dest, prospective_file)
        else:
            parser.print_usage()
            print('Try "{} --help" for help.\n'.format(parser.prog))
            parser.exit("Error: Unreadable file: {0}".format(prospective_file))


def cli():
    parser = argparse.ArgumentParser(
        prog='o2g',
        epilog='Here is a smile for you :)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Export GTFS feed from OpenStreetMap data.')
    parser.add_argument('osmfile', metavar='OSMFILE', action=readable_file,
                        nargs='?',
                        default=argparse.SUPPRESS,
                        help='an OSM data file supported by osmium')
    parser.add_argument('--area',
                        help='an OSM area name, e.g. Freiburg')
    parser.add_argument('--bbox',
                        help='a boundary box, e.g. 47.9485,7.7066,48.1161,8.0049')
    parser.add_argument('--outdir', action=readable_dir,
                        default='.',
                        help='output directory')
    parser.add_argument('--zipfile',
                        help='save to zipfile')
    parser.add_argument('--dummy', action='store_true',
                        default=False,
                        help='fill the missing parts with dummy data')
    parser.add_argument('--loglevel',
                        default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='the logging level')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + __version__,
                        help='show the version and exit')

    args = parser.parse_args()
    if not args.area and not args.bbox and not hasattr(args, 'osmfile'):
        parser.print_usage()
        parser.exit("o2g: error: one of these args are required: OSMFILE, bbox or area.")

    if args.loglevel:
        logging.basicConfig(level=args.loglevel)
    if hasattr(args, 'osmfile'):
        logging.debug('Input: %s', args.osmfile)
    logging.debug('Area: %s', args.area)
    logging.debug('Boundary box: %s', args.bbox)
    logging.debug('Output: %s', args.outdir)
    logging.debug('Zip?: %s', args.zipfile or False)
    logging.debug('Dummy?: %s', args.dummy)

    if args.area or args.bbox:
        filename, filepath = dl_osm_from_overpass(args.area, args.bbox)
        osmfile = filepath
    else:
        osmfile = args.osmfile

    main(osmfile, args.outdir, args.zipfile, args.dummy)


def main(osmfile, outdir, zipfile, dummy):
    start = time.time()

    with capture_logs() as logfile:
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
            writer.add_frequencies(dummy_data.frequencies)
            patched_agencies = gtfs_dummy.patch_agencies(tde.agencies)

        if patched_agencies:
            writer.add_agencies(patched_agencies)
        else:
            writer.add_agencies(tde.agencies)
        writer.add_stops(tde.stops)
        writer.add_routes(tde.routes)
        writer.add_shapes(tde.shapes)
        writer.add_feedinfo({
            'feed_publisher_name': 'Generated by o2g',
            'feed_publisher_url': 'hiposfer.com',
            'feed_lang': 'en',
            'feed_version': int(time.time())
        })

        writer.add_file('LICENSE', Path(__file__).parents[0] / 'ODbL-1.0.txt')
        writer.add_file('logs.txt', logfile)

    if zipfile:
        writer.write_zipped(os.path.join(outdir, zipfile))
        logging.info('GTFS feed saved in %s' % os.path.join(outdir, zipfile))
    else:
        writer.write_unzipped(outdir)
        logging.info('GTFS feed saved in %s' % outdir)

    logging.debug('Done in %d seconds.', (time.time() - start))


@contextmanager
def capture_logs():
    logfile = tempfile.mktemp()
    handler = FileHandler(logfile, mode='w')
    logging.getLogger().addHandler(handler)
    try:
        yield logfile
    finally:
        logging.getLogger().removeHandler(handler)


if __name__ == '__main__':
    cli()
