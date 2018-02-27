"""Tools to generate dummy GTFS feeds."""
import datetime
import logging

from collections import namedtuple


# Represents dummy GTFS data
DummyData = namedtuple('DummyData', ['calendar', 'shapes', 'stop_times', 'trips'])


def create_dummy_data(routes, stops, route_stops):
    """Create `calendar`, `stop_times`, `trips` and `shapes`.

    :return: DummyData namedtuple
    """
    calendar = _create_dummy_calendar()

    trips = \
        _create_dummy_trips(routes,
            stops,
            route_stops,
            calendar)

    stop_times = _create_dummy_stoptimes(trips, route_stops)

    shapes = create_shapes_and_update_trips(trips, stops, route_stops)

    return DummyData(calendar, shapes, stop_times, trips)


def monkey_patch_agencies(agencies):
    """Fill the fields that are necessary for passing transitfeed checks."""
    for agency in agencies.values():
        if 'agency_url' not in agency or not agency['agency_url']:
            agency['agency_url'] = 'http://hiposfer.com'
        #if 'agency_timezone' not in agency or not agency['agency_timezone']:
        # Set everything to one time zone to get rid of transitfeeds error.
        agency['agency_timezone'] = 'Europe/Berlin'


def _create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]


def _create_dummy_trips(routes, stops, route_stops, calendar):
    trips = []

    for route_id, route in routes.items():

        if len(route_stops.get(route_id, [])) < 2:
            continue

        cal_idx = 0
        for cal in calendar:
            # For the sake of simplicity, we assume a fixed number of trips per service day.
            # Even though in reality there are less number of trips on weekends and holidays.
            # We assume trips begin from 5:00 AM and run untill 11:00 PM and there is one trip
            # every 20 minutes. Therefore in total we add 54 trips per route per service day.
            # 18 service hours per day * 3 trips per hour = 54
            for idx in range(54):

                trip_id = \
                    '{route_id}.{cal_idx}{sequence}'.format(route_id=route_id,
                        cal_idx=cal_idx,
                        sequence=idx+1)

                trip = {'route_id': route_id,
                        'service_id': cal['service_id'],
                        'trip_id': trip_id,
                        'trip_headsign': '[Dummy]{}'.format(route['route_long_name']),
                        # Leave shape_id empty. Fill it later for trips which have enough info.
                        'shape_id': '',
                        # Used for generating stop times.
                        'sequence': idx}
                trips.append(trip)
            # Increase the calendar index, just for making the trip_id.
            cal_idx += 1

    return trips


def _create_dummy_stoptimes(trips, route_stops):
    stoptimes = []

    for trip in trips:
        stoptimes.extend(
            _create_dummy_trip_stoptimes(trip['trip_id'],
                route_stops.get(trip['route_id'], []),
                trip['sequence']))

    return stoptimes


def _create_dummy_trip_stoptimes(trip_id, stop_ids, sequence):
    """Create station stop times for each trip."""
    delta = datetime.timedelta(minutes=20)
    offset = sequence*delta
    waiting = datetime.timedelta(seconds=30)

    first_service_time = datetime.datetime(2017, 1, 1, 5, 0, 0) + offset

    stop_sequence = 0
    arrival = first_service_time
    last_departure_hour = (arrival + waiting).hour

    for stop_id in stop_ids:

        departure = arrival + waiting

        if arrival.hour < last_departure_hour:
            arrival_hour = arrival.hour + 24
            departure_hour = departure.hour + 24
            last_departure_hour = departure.hour + 24
        else:
            arrival_hour = arrival.hour
            departure_hour = departure.hour
            last_departure_hour = departure.hour

        yield {'trip_id': trip_id,
               'arrival_time': '{:02}:{}'.format(arrival_hour, arrival.strftime('%M:%S')),
               'departure_time': '{:02}:{}'.format(departure_hour, departure.strftime('%M:%S')),
               'stop_id': stop_id,
               'stop_sequence': stop_sequence}

        stop_sequence += 1
        arrival += delta


def create_shapes_and_update_trips(trips, stops, route_stops):
    """Create a list of shape records for each trip."""
    shapes = []
    for trip in trips:
        trip_id = trip['trip_id']
        trip_stop_ids = route_stops[trip['route_id']]

        # Check whether all necessary stop nodes are available
        if _are_stop_nodes_available(trip_id, stops, trip_stop_ids):
            # Now that we are sure the necessary information for each stop of the trip exists,
            # we prooceed to creating shape records for this trip.
            shape_id = '{}{}'.format(trip_id, trip['route_id'])
            sequence_id = 0
            for stop_id in trip_stop_ids:
                stop = stops[stop_id]
                shapes.append(
                    {'shape_id': shape_id,
                     'shape_pt_lat': stop['stop_lat'],
                     'shape_pt_lon': stop['stop_lon'],
                     'shape_pt_sequence': sequence_id})
                sequence_id += 1

            # Eventually update the trip to reflect the shape_id
            trip['shape_id'] = shape_id

    return shapes


def _are_stop_nodes_available(trip_id, stops, trip_stop_ids):
    for stop_id in trip_stop_ids:
        # This means we are dealing with a route which not all of its stops are loaded.
        # We can't create a shape for a route that we don't have lon and lat of all of
        # its stops. Probably those information were not availabe in the OSM file used
        # to generate current feed.
        if stop_id not in stops:
            logging.debug('Stop {} is required to build shape for trip {}.'.format(stop_id, trip_id))
            return False# No shapes for this trip.
    return True
