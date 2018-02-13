"""Tools to generate dummy GTFS feeds."""
import datetime
import logging


def populate_dummy_data(writer, processor):
    calendar = _create_dummy_calendar()
    trips, stoptimes = _create_dummy_trips_and_stoptimes(processor, calendar)
    writer.add_trips(trips)
    writer.add_stop_times(stoptimes)
    writer.add_calendar(calendar)


def _create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]


def _create_dummy_trips_and_stoptimes(processor, calendar):
    trips = []
    stoptimes = []
    for route_id, route in processor.routes.items():
        for cal in calendar:
        # For the sake of simplicity, we assume a fixed number of trips per service day.
        # Even though in reality there are less number of trips on weekends and holidays.
        # We assume trips begin from 5:00 AM and run untill 11:00 PM and there is one trip
        # every 20 minutes. Therefore in total we add 54 trips per route per service day.
        # 18 service hours per day * 3 trips per hour = 54
            for idx in range(54):
                trip_id = '{route_id}{sequence}'.format(route_id=route_id, sequence=idx+1)
                trip = {'route_id': route_id,
                        'service_id': cal['service_id'],
                        'trip_id': trip_id,
                        'trip_headsign': '[Dummy]{}'.format(route['route_long_name']),
                        'shape_id': route_id}
                trips.append(trip)
                stoptimes.extend(_create_dummy_trip_stoptimes(trip, idx, processor))
    return trips, stoptimes


def _create_dummy_trip_stoptimes(trip, sequence, processor):
    """Create station stop times for each trip."""
    # stops = find stops that belong to this route (trip)
    # needs trip_id and stop_id
    delta = datetime.timedelta(minutes=20)
    offset = sequence*datetime.timedelta(minutes=20)
    waiting = datetime.timedelta(seconds=30)

    first_service_time = datetime.datetime(2017, 1, 1, 5, 0, 0) + offset

    stop_sequence = 0
    arrival = first_service_time
    for stop in _get_route_stops(trip['route_id'], processor):
        departure = arrival + waiting
        yield {'trip_id': trip['trip_id'],
               'arrival_time': arrival.strftime('%H:%M:%S'),
               'departure_time': departure.strftime('%H:%M:%S'),
               'stop_id': stop['stop_id'],
               'stop_sequence': stop_sequence}
        stop_sequence += 1
        arrival += delta


def _get_route_stops(route_id, processor):
    # Node: there are routes that are not present in route_stops,
    # the reason is, we have processed every node in the OSM data
    # to find stops, without filtering out anything. However,
    # apparently not all of those stops belong to transport
    # relations. Remember that we have filtered relations in favor
    # of transport means (bus, tram, train). Therefore we have
    # some inconsistencies here.
    # Moreover, it could simply be a bug in finding stops.
    # Even more, it could be that the route is streched among
    # multiple regions and we simply have not loaded that data.
    # For example, see relation 1686600807 which is an ICE train
    # from Hamburg to Köln when processing Bremen OSM data.
    if route_id not in processor.route_stops:
        logging.debug('No stops information for route %s', route_id)
        return
    else:
        for stop_id in processor.route_stops[route_id]:
            yield processor.stops[stop_id]
