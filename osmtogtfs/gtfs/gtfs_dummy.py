"""Tools to generate dummy GTFS feeds."""
import datetime
from math import radians, cos, sin, asin, sqrt
from collections import namedtuple, defaultdict

from osmtogtfs.osm.models import Agency


# Represents dummy GTFS data
DummyData = namedtuple('DummyData',
                       ['calendar', 'stop_times', 'trips', 'frequencies'])


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
    frequencies = _create_dummy_frequencies(trips)

    return DummyData(calendar, stop_times, trips, frequencies)


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
            # For the sake of simplicity, we assume 3 trips per service day.
            for idx in range(3):

                trip_id = \
                    '{sequence}{cal_idx}.{route_id}'.format(
                        sequence=idx + 1,
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
        # One service every 20 minutes from the base station
        first_service_time = \
            datetime.datetime(2017, 1, 1, 5, 0, 0) + \
            datetime.timedelta(minutes=20) * trip['sequence']
        stoptimes.extend(
            _create_dummy_trip_stoptimes(
                trip['trip_id'],
                stops_per_route.get(trip['route_id'], []),
                first_service_time))

    return stoptimes


def _create_dummy_trip_stoptimes(trip_id, stops, first_service_time):
    """Create station stop times for each trip."""
    waiting = datetime.timedelta(seconds=30)
    arrival = first_service_time
    last_departure = first_service_time
    last_departure_hour = (arrival + waiting).hour
    last_stop = None

    departure_hour = None
    arrival_hour = None
    for stop_sequence, stop in enumerate(stops):

        # Avoid time travels
        arrival = last_departure + get_time_from_last_stop(last_stop, stop)
        departure = arrival + waiting

        # Cover the case when the arrival time falls into the next day
        if arrival.hour < last_departure_hour:
            diff = last_departure_hour
            arrival_hour = arrival.hour + diff
            departure_hour = departure.hour + diff
            last_departure_hour = departure.hour + diff
        else:
            arrival_hour = arrival.hour
            departure_hour = departure.hour
            last_departure_hour = departure.hour

        # Cover the case when adding waiting time to the arrival time
        # falls into the next day
        if departure.hour < arrival.hour:
            diff = last_departure_hour
            departure_hour = departure.hour + diff
            last_departure_hour = departure.hour + diff

        yield {'trip_id': trip_id,
               'arrival_time': '{:02}:{}'.format(
                   arrival_hour,
                   arrival.strftime('%M:%S')),
               'departure_time': '{:02}:{}'.format(
                   departure_hour,
                   departure.strftime('%M:%S')),
               'stop_id': stop.stop_id,
               'stop_sequence': stop_sequence}

        last_stop = stop
        last_departure = departure


def get_time_from_last_stop(src_stop, dst_stop):
    if not src_stop:
        return datetime.timedelta()

    # Average public transport speed
    average_speed_kmh = 20

    distance_km = \
        haversine(src_stop.stop_lon,
                  src_stop.stop_lat,
                  dst_stop.stop_lon,
                  dst_stop.stop_lat)
    return \
        datetime.timedelta(
            hours=distance_km/average_speed_kmh)


# https://stackoverflow.com/a/4913653
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two
    points on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r


def _create_dummy_frequencies(trips):
    """Create station stop frequencies."""
    for trip in trips:
        yield {'trip_id': trip['trip_id'],
               'start_time': '04:30:00',
               'end_time': '08:30:00',
               'headway_secs': '1200'}
        yield {'trip_id': trip['trip_id'],
               'start_time': '08:30:00',
               'end_time': '20:30:00',
               'headway_secs': '1800'}
        yield {'trip_id': trip['trip_id'],
               'start_time': '20:30:00',
               'end_time': '25:30:00',
               'headway_secs': '2800'}
