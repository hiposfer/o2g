"""Tools to generate dummy GTFS feeds."""
import datetime
from time import gmtime, strftime


def populate_dummy_data(processor, writer, routes):
    calendar = _create_dummy_calendar()
    trips = _create_dummy_trips(routes, calendar)
    writer.add_trips(trips)
    writer.add_stop_times(_create_dummy_stoptimes(trips, processor.stops))
    writer.add_calendar(calendar)


def _create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]


def _create_dummy_trips(routes, calendar):
    trips = []
    for route in routes:
        for cal in calendar:
        # TODO: Create multiple dummy trips per route, e.g. every 20 minutes
            trips.append(
                {'route_id': route['route_id'],
                 'service_id': cal['service_id'],
                 'trip_id': 'trp_{}'.format(route['route_id']),
                 'trip_headsign': 'Dummy Trip',
                 'shape_id': 'shp_{}'.format(route['route_id'])}
                )
    return trips


def _create_dummy_stoptimes(trips, stops):
    """Create station stop times for each trip."""
    # stops = find stops that belong to this route (trip)
    # needs trip_id and stop_id
    first_service_time = datetime.datetime(2017, 1, 1, 5, 0, 0)
    for trip in trips:
        stop_sequence = 0
        arrival = first_service_time
        for stop in _get_route_stops(trip['route_id'], stops):
            departure = arrival + datetime.timedelta(seconds=30)
            yield {'trip_id': trip['trip_id'],
                   'arrival_time': arrival.strftime('%H:%M:%S'),
                   'departure_time': departure.strftime('%H:%M:%S'),
                   'stop_id': stop['stop_id'],
                   'stop_sequence': stop_sequence}
            stop_sequence += 1
            arrival += datetime.timedelta(minutes=20)
        first_service_time += datetime.timedelta(minutes=20)


def _get_route_stops(route_id, stops):
    #return filter(lambda x: x['route_id'] == route_id, stops.values())
    return [stop for stop in stops.values() if stop['route_id'] == route_id]
