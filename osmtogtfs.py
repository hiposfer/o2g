#!env python
"""
Extracts partial GTFS data from OSM file.
"""
import sys
import time

from osm_processor import GTFSPreprocessor
from gtfs_writer import GTFSWriter, GTFSRouteType


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
    writer.write_feed('gtfs.zip')
    print('GTFS feed was written to gtfs.zip file.')