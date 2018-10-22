"""Utilities for writing GTFS feeds."""
import os
import io
import csv
import shutil
import zipfile
from collections import OrderedDict


class GTFSWriter(object):
    """GTFS feed writer."""
    def __init__(self):
        self._buffers = {}
        self._csv_writers = {}
        self._files = {}

        for name, csv_headers in self.headers.items():
            self._buffers[name] = io.StringIO()
            self._csv_writers[name] =\
                csv.writer(self._buffers[name], lineterminator='\n')
            self._csv_writers[name].writerow(csv_headers)

    def _add_records(self, name, records, sortkey=None):
        if sortkey:
            records = sorted(records, key=lambda x: x[sortkey])
        for rec in records:
            if not isinstance(rec, dict):
                record = rec._asdict()
            else:
                record = rec
            csv_record = OrderedDict.fromkeys(self.headers[name])
            # Update csv with keys present in headers. Skip anything else.
            csv_record.update(
                {k: v for k, v in record.items() if k in self.headers[name]})
            self._csv_writers[name].writerow([v for v in csv_record.values()])

    @property
    def headers(self):
        """Map of filename to headers for every GTFS file.

        Only headers present in this map will be considered."""
        return {
            'agency': ['agency_id', 'agency_name', 'agency_url',
                       'agency_timezone', 'agency_lang', 'agency_phone',
                       'agency_fare_url', 'agency_email'],

            'stops': ['stop_id', 'stop_code', 'stop_name', 'stop_desc',
                      'stop_lat', 'stop_lon', 'zone_id', 'stop_url',
                      'location_type', 'parent_station', 'stop_timezone',
                      'wheelchair_boarding'],

            'routes': ['route_id', 'agency_id', 'route_short_name',
                       'route_long_name', 'route_desc', 'route_type',
                       'route_url', 'route_color', 'route_text_color'],

            'trips': ['route_id', 'service_id', 'trip_id', 'trip_headsign',
                      'shape_id'],

            'calendar': ['service_id', 'monday', 'tuesday', 'wednesday',
                         'thursday',
                         'friday', 'saturday', 'sunday', 'start_date',
                         'end_date'],

            'stop_times': ['trip_id', 'arrival_time', 'departure_time',
                           'stop_id',
                           'stop_sequence'],

            'shapes': ['shape_id', 'shape_pt_lat', 'shape_pt_lon',
                       'shape_pt_sequence'],

            'frequencies': ['trip_id', 'start_time', 'end_time',
                            'headway_secs']}

    def add_agencies(self, agencies):
        self._add_records('agency', agencies)

    def add_stops(self, stops):
        self._add_records('stops', stops)

    def add_routes(self, routes):
        self._add_records('routes', routes, sortkey=0)

    def add_calendar(self, weekly_schedules):
        self._add_records('calendar', weekly_schedules)

    def add_trips(self, trips):
        self._add_records('trips', trips)

    def add_stop_times(self, stop_times):
        self._add_records('stop_times', stop_times)

    def add_shapes(self, shapes):
        self._add_records('shapes', shapes)

    def add_frequencies(self, frequencies):
        self._add_records('frequencies', frequencies)

    def add_file(self, name, path):
        self._files[name] = path

    def write_zipped(self, filepath):
        """Write the GTFS feed in the given file."""
        with zipfile.ZipFile(filepath, mode='w', compression=zipfile.ZIP_DEFLATED) as zfile:
            for name, buffer in self._buffers.items():
                encoded_values = io.BytesIO(buffer.getvalue().encode('utf-8'))
                zfile.writestr('{}.txt'.format(name),
                               encoded_values.getbuffer())
            for name, path in self._files.items():
                zfile.write(path, arcname=name)

    def write_unzipped(self, destination):
        """Write GTFS text files in the given path."""
        for name, buffer in self._buffers.items():
            with open(os.path.join(destination,
                                   '{}.txt'.format(name)),
                      'w', encoding='utf-8') as file:
                file.write(buffer.getvalue())
        for name, path in self._files.items():
            shutil.copy(path, os.path.join(destination, name))
