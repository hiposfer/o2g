"""overpass and osm download functions"""
import os
import pathlib
import tempfile
import urllib
from urllib.request import urlopen


def dl_osm_from_overpass(area, bbox):
    if not area and not bbox:
        raise Exception('At lease area or bbox must be given.')

    overpass_query = build_overpass_query(area, bbox)
    overpass_api_url = "http://overpass-api.de/api/interpreter"

    filepath = tempfile.mktemp(suffix='_overpass.osm')
    resp = urlopen(overpass_api_url, overpass_query.encode('utf-8'))

    if resp.status == 200:
        with open(filepath, 'w') as osm:
            osm.write(resp.read().decode('utf-8'))
        return os.path.split(filepath)[-1], filepath
    else:
        raise urllib.request.HTTPError(
            'Error calling Overpass API. Status: {}, reason: {}'.format(
                resp.status, resp.reason))

    raise Exception("Can't download data form overpass api.")


def build_overpass_query(area, bbox):
    template = """
    {bbox}
    {area}
    (
      rel
        [!"deleted"]
        ["type"="route"]
        ["route"~"tram|subway|bus|ex-bus|light_rail|rail|railway"]
        {area_limit};
      rel
        [!"deleted"]
        ["type"="public_transport"]
        ["public_transport"="stop_area"]
        {area_limit};
    );
    out body;

    way(r){area_limit};
    out body;

    node(w){area_limit};
    out body;
    """
    bbox_fmt = ''
    area_fmt = ''
    area_limit_fmt = ''

    if bbox:
        south, west, north, east = bbox.split(',')
        bbox_fmt = '[bbox:{},{},{},{}];'.format(south, west, north, east)

    if area:
        area_fmt = 'area["name"="{}"]->.searchArea;'.format(area)
        area_limit_fmt = '(area.searchArea)'

    return template.format(
        bbox=bbox_fmt, area=area_fmt, area_limit=area_limit_fmt)


def dl_osm_from_url(url):
    filename = tempfile.mktemp(suffix=pathlib.Path(url).name)
    filepath, headers =\
        urllib.request.urlretrieve(url, filename=filename)
    return pathlib.Path(url).name, filepath
