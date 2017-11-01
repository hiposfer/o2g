#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import os
import sys
import time
import tempfile

from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter, GTFSRouteType


def _make_gtfs_filename(input_filename):
    base = os.path.split(input_filename)[-1][:10]
    return "{base}_{slug}.gtfs.zip".format(
        base=base,
        slug=os.path.split(tempfile.mktemp())[-1])

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python osmtogtfs.py <osmfile>")
        sys.exit(-1)

    h = GTFSPreprocessor()

    start = time.time()
    h.apply_file(sys.argv[1], locations=True, idx='sparse_mem_array')
    print("Preprocessing tooke %d seconds." % (time.time() - start))

    writer = GTFSWriter()
    writer.add_agencies(h.agencies.values())
    writer.add_stops(h.stops.values())
    supported_routes = [r for r in h.all_routes if r['route_type'] in\
        [GTFSRouteType.Bus.value,
         GTFSRouteType.Tram.value,
         GTFSRouteType.Subway.value,
         GTFSRouteType.Rail.value]]
    writer.add_routes(supported_routes)
    filename = _make_gtfs_filename(sys.argv[1])
    writer.write_feed(filename)
    print('GTFS feed saved in %s' % filename)
