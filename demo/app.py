"""osmtogtfs web app"""
import os
import pathlib
import tempfile
import urllib.parse
import urllib.request


from bottle import run, template, request, static_file, abort, default_app

import requests
import validators

from osmtogtfs.cli import main


UPLOAD_DIR = '/tmp'
app = default_app()


@app.get('/')
def index():
    return template('index.html', messages=[])


@app.post('/')
def do_index():
    uploaded_filepath = \
        save_file(request.files['file']) if 'file' in request.files else None

    url = request.forms.get('url')

    if not url and not uploaded_filepath:
        return template('index.html', messages=['Provide a URL or upload a file.'])

    if not uploaded_filepath and not validators.url(url):
        return template('index.html', messages=['Not a valid URL.'])

    filename = uploaded_filepath or dl_osm_from_url(url)
    zipfile = create_zipfeed(filename, bool(request.forms.get('dummy')))

    return static_file(os.path.split(zipfile)[-1], root=UPLOAD_DIR, download=True)


def save_file(file):
    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_DIR, filename)
        file.save(filepath, overwrite=True)
        return filepath


def create_zipfeed(filename, dummy=False):
    zipfile = '{}.zip'.format(filename)
    print('Writing GTFS feed to %s' % zipfile)
    main(filename, '.', zipfile, dummy)
    return zipfile


@app.get('/o2g', methods=['GET'])
def o2g():
    area = request.args.get('area')
    bbox = request.args.get('bbox')
    url = request.args.get('url')

    if area or bbox:
        filepath = dl_osm_from_overpass(area, bbox)
    elif url and validators.url(url):
        filepath = dl_osm_from_url(url)
    else:
        abort(400)

    zipfile = create_zipfeed(
        filepath,
        bool(request.args.get('dummy')))

    return static_file(
        os.path.split(zipfile)[-1],
        root=UPLOAD_DIR,
        #mimetype='application/zip',
        download=True)


def dl_osm_from_overpass(area, bbox):
    if not area and not bbox:
        raise Exception('At lease area or bbox must be given.')

    overpass_query = build_overpass_query(area, bbox)
    overpass_api = "http://overpass-api.de/api/interpreter"

    filename = tempfile.mktemp(suffix='_overpass.osm')
    resp = requests.post(overpass_api, data=overpass_query)
    if resp.ok:
        with open(filename, 'w') as osm:
            osm.write(resp.content.decode('utf-8'))
        return filename
    else:
        resp.raise_for_status()

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
    (._; >;);
    out;
    """
    bbox_fmt = ''
    area_fmt = ''
    area_limit_fmt = ''

    if bbox:
        south, west, north, east = bbox.split(',')
        bbox_fmt ='[bbox:{},{},{},{}];'.format(south, west, north, east)

    if area:
        area_fmt ='area["name"="{}"];'.format(area)
        area_limit_fmt ='(area._)'

    return template.format(bbox=bbox_fmt, area=area_fmt, area_limit=area_limit_fmt)


def dl_osm_from_url(url):
    filename = tempfile.mktemp(suffix=pathlib.Path(url).name)
    local_filename, headers =\
        urllib.request.urlretrieve(url, filename=filename)
    print(local_filename, headers)
    return local_filename


if __name__ == '__main__':
    run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=True)
