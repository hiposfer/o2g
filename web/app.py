"""o2g web interface"""
import os
import tempfile
from urllib.parse import urlparse

from bottle import run, template, request, static_file, abort, default_app

from o2g.cli import main
from o2g.web import dl_osm_from_overpass, dl_osm_from_url

app = default_app()


@app.get('/')
def index():
    return template('index.html', messages=[])


@app.post('/')
def do_index():
    file = request.files.get('file')
    url = request.forms.get('url')

    if not url and not file:
        return template('index.html', messages=['Provide a URL or upload a file.'])

    if not file and url and not is_valid_url(url):
        return template('index.html', messages=['Not a valid URL.'])

    if file:
        filename = file.filename
        filepath = save_file(file)
    elif url:
        filename, filepath = dl_osm_from_url(url)

    return send_feed(
        filepath,
        filename + '.gtfs.zip',
        dummy=bool(request.forms.get('dummy')))


def is_valid_url(url):
    return urlparse(url).scheme in ('http', 'https')


def save_file(file):
    fd, filepath = tempfile.mkstemp(suffix=file.filename)
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


if __name__ == '__main__':
    run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=True)
