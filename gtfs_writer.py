"""Utilities for writing GTFS feeds."""
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
        self._agencies_writer = csv.writer(self._agencies_buffer)
        self._agencies_writer.writerow(self._agencies_headers)
        
        # self._stops_required_headers = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
        self._stops_headers = ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon',
                               'zone_id', 'stop_url', 'location_type', 'parent_station', 'stop_timezone', 'wheelchair_boarding']
        self._stops_buffer = io.StringIO()
        self._stops_writer = csv.writer(self._stops_buffer)
        self._stops_writer.writerow(self._stops_headers)

        # self._routes_required_headers = ['route_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'agency_id']
        self._routes_headers = ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type',
                                'route_url', 'route_color', 'route_text_color']
        self._routes_buffer = io.StringIO()
        self._routes_writer = csv.writer(self._routes_buffer)
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
        
    def write_feed(self, filename):
        with zipfile.ZipFile(filename, mode='x') as z:
            agencies = io.BytesIO(self._agencies_buffer.getvalue().encode('utf-8'))
            z.writestr('agency.txt', agencies.getbuffer())
            stops = io.BytesIO(self._stops_buffer.getvalue().encode('utf-8'))
            z.writestr('stops.txt', stops.getbuffer())
            routes = io.BytesIO(self._routes_buffer.getvalue().encode('utf-8'))
            z.writestr('routes.txt', routes.getbuffer())
