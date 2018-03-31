"""Tools to generate dummy GTFS feeds."""
import datetime
from collections import namedtuple, defaultdict

from osmtogtfs.osm.models import Agency


# Represents dummy GTFS data
DummyData = namedtuple('DummyData', ['calendar', 'stop_times', 'trips'])


def create_dummy_data(routes, stops):
    """Create `calendar`, `stop_times`, `trips` and `shapes`.

    :return: DummyData namedtuple
    """
    # Build stops per route auxiliary map
    stops_per_route = defaultdict(lambda: [])
    stops_map = {}
    for s in stops:
        stops_per_route[s.route_id].append(s)
        stops_map[s.stop_id] = s

    calendar = _create_dummy_calendar()

    trips = \
        _create_dummy_trips(
            routes,
            stops_per_route,
            calendar)

    stop_times = _create_dummy_stoptimes(trips, stops_per_route)

    return DummyData(calendar, stop_times, trips)


def patch_agencies(agencies):
    """Fill the fields that are necessary for passing transitfeed checks."""
    # First return the unknown agency entry
    yield Agency(-1, 'http://hiposfer.com', 'Unknown agency', 'Europe/Berlin')

    # Then return the rest.
    for agency_id, agency_url, agency_name, agency_timezone in agencies:
        if not agency_url:
            agency_url = 'http://hiposfer.com'
        if not agency_timezone:
            # Set everything to one time zone to get rid of transitfeeds error.
            agency_timezone = 'Europe/Berlin'
        yield Agency(agency_id, agency_url, agency_name, agency_timezone)


def _create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0,
             'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101,
             'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1,
             'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101,
             'end_date': 20190101}]


def _create_dummy_trips(routes, stops_per_route, calendar):
    trips = []

    for route in routes:
        route_id = route.route_id

        if len(stops_per_route.get(route_id, [])) < 2:
            continue

        for cal_idx, cal in enumerate(calendar):
            # For the sake of simplicity, we assume a fixed number of trips per service day.
            # Even though in reality there are less number of trips on weekends and holidays.
            # We assume trips begin from 5:00 AM and run untill 11:00 PM and there is one trip
            # every 20 minutes. Therefore in total we add 54 trips per route per service day.
            # 18 service hours per day * 3 trips per hour = 54
            for idx in range(54):

                trip_id = \
                    '{sequence}{cal_idx}.{route_id}'.format(
                        sequence=idx+1,
                        cal_idx=cal_idx,
                        route_id=route_id)

                trip = {'route_id': route_id,
                        'service_id': cal['service_id'],
                        'trip_id': trip_id,
                        'trip_headsign':
                            '[Dummy]{}'.format(route.route_long_name),
                        # Use route_id, i.e. relation_id as shape_id
                        'shape_id': route_id,
                        # Used for generating stop times.
                        'sequence': idx}
                trips.append(trip)

    return trips


def _create_dummy_stoptimes(trips, stops_per_route):
    stoptimes = []

    for trip in trips:
        stoptimes.extend(
            _create_dummy_trip_stoptimes(
                trip['trip_id'],
                stops_per_route.get(trip['route_id'], []),
                trip['sequence']))

    return stoptimes


def _create_dummy_trip_stoptimes(trip_id, stops, sequence):
    """Create station stop times for each trip."""
    delta = datetime.timedelta(minutes=20)
    offset = sequence*delta
    waiting = datetime.timedelta(seconds=30)

    first_service_time = datetime.datetime(2017, 1, 1, 5, 0, 0) + offset

    arrival = first_service_time
    last_departure_hour = (arrival + waiting).hour

    for stop_sequence, stop in enumerate(stops):

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
               'arrival_time': '{:02}:{}'.format(
                    arrival_hour,
                    arrival.strftime('%M:%S')),
               'departure_time': '{:02}:{}'.format(
                    departure_hour,
                    departure.strftime('%M:%S')),
               'stop_id': stop.stop_id,
               'stop_sequence': stop_sequence}

        arrival += delta
