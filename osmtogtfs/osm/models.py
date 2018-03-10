from collections import namedtuple


Node = namedtuple('Node', ['id', 'lon', 'lat', 'tags'])
Way = namedtuple('Way', ['id', 'points'])
Relation = namedtuple('Relation', ['id', 'tags', 'member_info'])


Point = namedtuple('Point', ['lon', 'lat'])

Agency = namedtuple('Agency', [
    'agency_id',
    'agency_url',
    'agency_name',
    'agency_timezone'])

Route = namedtuple('Route', [
    'route_id',
    'route_short_name',
    'route_long_name',
    'route_type',
    'route_url',
    'route_color',
    'agency_id'])

Stop = namedtuple('Stop', [
    'stop_id',
    'stop_name',
    'stop_lon',
    'stop_lat',
    'route_id'])

Shape = namedtuple('Shape', [
    'shape_id',
    'shape_pt_lat',
    'shape_pt_lon',
    'shape_pt_sequence'])
