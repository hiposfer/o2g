"""osmtogtfs web app"""
import os
import pathlib
import tempfile
import urllib
from urllib.parse import urlparse
from urllib.request import urlopen

from bottle import run, template, request, static_file, abort, default_app

from osmtogtfs.cli import main


UPLOAD_DIR = '/tmp'
app = default_app()


@app.get('/')
def index():
    return template('index.html', messages=[])


@app.post('/')
def do_index():
    filepath = \
        save_file(request.files['file']) if 'file' in request.files else None

    url = request.forms.get('url')

    if not url and not filepath:
        return template('index.html', messages=['Provide a URL or upload a file.'])

    if not filepath and not is_valid_url(url):
        return template('index.html', messages=['Not a valid URL.'])

    if not filepath:
        dl_filename, dl_filepath = dl_osm_from_url(url)

    filename = os.path.split(filepath)[-1] if filepath else dl_filename
    return send_feed(
        filepath or dl_filepath,
        filename + '.gtfs.zip',
        dummy=bool(request.forms.get('dummy')))


def is_valid_url(url):
    return urlparse(url).scheme in ('http', 'https')


def save_file(file):
    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_DIR, filename)
        file.save(filepath, overwrite=True)
        return filepath


def send_feed(filepath, filename=None, dummy=False):
    zipfile = create_zipfeed(filepath, dummy)
    if not filename:
        filename = os.path.split(zipfile)[-1]

    return static_file(
        os.path.split(zipfile)[-1],
        root=os.path.split(zipfile)[0],
        download=filename,
        mimetype='application/zip')


def create_zipfeed(filename, dummy=False):
    zipfile = '{}.zip'.format(filename)
    print('Writing GTFS feed to %s' % zipfile)
    main(filename, '.', zipfile, dummy)
    return zipfile


@app.get('/o2g', methods=['GET'])
def o2g():
    area = request.params.get('area')
    bbox = request.params.get('bbox')
    url = request.params.get('url')

    if area or bbox:
        filename, filepath = dl_osm_from_overpass(area, bbox)
        if area:
            filename = area + '_overpass'
    elif url and is_valid_url(url):
        filename, filepath = dl_osm_from_url(url)
    else:
        abort(400)

    return send_feed(
        filepath,
        filename + '.gtfs.zip',
        dummy=bool(request.params.get('dummy')))


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

    return template.format(bbox=bbox_fmt, area=area_fmt, area_limit=area_limit_fmt)


def dl_osm_from_url(url):
    filename = tempfile.mktemp(suffix=pathlib.Path(url).name)
    filepath, headers =\
        urllib.request.urlretrieve(url, filename=filename)
    print(filepath, headers)
    return pathlib.Path(url).name, filepath


if __name__ == '__main__':
    run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=True)
