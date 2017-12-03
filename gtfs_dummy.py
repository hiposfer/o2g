"""Tools to generate dummy GTFS feeds."""
def populate_dummy_data(processor, writer, routes):
    calendar = create_dummy_calendar()
    trips = create_dummy_trips(routes, calendar)
    writer.add_trips(trips)
    writer.add_stop_times(create_dummy_stoptimes(trips))
    writer.add_calendar(calendar)


def create_dummy_trips(routes, calendar):
    for route in routes:
        for cal in calendar:
            yield {'route_id': route['route_id'],
                   'service_id': cal['service_id'],
                   'trip_id': 'trp_{}'.format(route['route_id']),
                   'shape_id': 'shp_{}'.format(route['route_id'])}


def create_dummy_stoptimes(trips):
    for trip in trips:
        yield {'trip_id': trip['trip_id'],
               'arrival_time': '0:06:10',
               'departure_time': '0:06:10',
               'stop_id': '',
               'stop_sequence': ''}


def create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]
