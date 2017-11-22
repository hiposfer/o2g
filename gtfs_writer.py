"""Utilities for writing GTFS feeds."""
import os
import io
import csv
import enum
import zipfile
from collections import OrderedDict


class GTFSRouteType(enum.Enum):
    Tram = 0
    Subway = 1
    Rail = 2
    Bus = 3
    Ferry = 4
    CableCar = 5
    Gondola = 6
    Funicular = 7


class GTFSWriter(object):
    """GTFS feed writer."""
    def __init__(self):
        # self._agencies_required_headers = ['agency_name', 'agency_url', 'agency_timezone']
        self._agencies_headers = ['agency_id', 'agency_name', 'agency_url', 'agency_timezone',
                                  'agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email']
        self._agencies_buffer = io.StringIO()
        self._agencies_writer = csv.writer(self._agencies_buffer, lineterminator='\n')
        self._agencies_writer.writerow(self._agencies_headers)
        
        # self._stops_required_headers = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
        self._stops_headers = ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon',
                               'zone_id', 'stop_url', 'location_type', 'parent_station', 'stop_timezone', 'wheelchair_boarding']
        self._stops_buffer = io.StringIO()
        self._stops_writer = csv.writer(self._stops_buffer, lineterminator='\n')
        self._stops_writer.writerow(self._stops_headers)

        # self._routes_required_headers = ['route_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'agency_id']
        self._routes_headers = ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type',
                                'route_url', 'route_color', 'route_text_color']
        self._routes_buffer = io.StringIO()
        self._routes_writer = csv.writer(self._routes_buffer, lineterminator='\n')
        self._routes_writer.writerow(self._routes_headers)

    def add_agencies(self, agencies):
        for agency in agencies:
            record = OrderedDict.fromkeys(self._agencies_headers, '')
            record.update(agency)
            self._agencies_writer.writerow([v for v in record.values()])

    def add_stops(self, stops):
        for stop in stops:
            record = OrderedDict.fromkeys(self._stops_headers, '')
            record.update(stop)
            self._stops_writer.writerow([v for v in record.values()])

    def add_routes(self, routes):
        for route in routes:
            record = OrderedDict.fromkeys(self._routes_headers, '')
            record.update(route)
            self._routes_writer.writerow([v for v in record.values()])
        
    def write_zipped(self, filename):
        with zipfile.ZipFile(filename, mode='w') as z:
            self._write_to_zipfile(z, self._agencies_buffer, 'agency.txt')
            self._write_to_zipfile(z, self._stops_buffer, 'stops.txt')
            self._write_to_zipfile(z, self._routes_buffer, 'routes.txt')

    def _write_to_zipfile(self, zipfile, buffer, filename):
        encoded_values = io.BytesIO(buffer.getvalue().encode('utf-8'))
        zipfile.writestr(filename, encoded_values.getbuffer())

    def write_unzipped(self, path):
        self._write_file(self._agencies_buffer, os.path.join(path, 'agency.txt'))
        self._write_file(self._stops_buffer, os.path.join(path, 'stops.txt'))
        self._write_file(self._routes_buffer, os.path.join(path, 'routes.txt'))

    def _write_file(self, buffer, endpoint):
        with open(endpoint, 'w', encoding='utf-8') as f:
            f.write(buffer.getvalue())
