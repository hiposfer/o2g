"""osmtogtfs web app"""
import pathlib
import tempfile
import urllib.parse
import urllib.request

import validators
from flask import Flask, request, send_file, render_template

from osmtogtfs.gtfs import gtfs_dummy
from osmtogtfs.gtfs.gtfs_writer import GTFSWriter
from osmtogtfs.osm.exporter import TransitDataExporter


app = Flask(__name__)
application = app


@app.route('/')
def index():
    url = request.args.get('url')
    if not url:
        return render_template('index.html')

    if not validators.url(url):
        return "Not a valid URL."

    filename = dl_osm(url)
    zipfile = create_zipfeed(filename, bool(request.args.get('dummy')))

    print(zipfile)
    print(pathlib.Path(zipfile).name)

    return send_file(
        zipfile,
        attachment_filename=pathlib.Path(zipfile).name,
        as_attachment=True)


def dl_osm(url):
    filename = tempfile.mktemp(suffix=pathlib.Path(url).name)
    local_filename, headers =\
        urllib.request.urlretrieve(url, filename=filename)
    print(local_filename, headers)
    return local_filename


def create_zipfeed(filename, dummy=False):
    tde = TransitDataExporter(filename)
    tde.process()

    writer = GTFSWriter()
    patched_agencies = None
    if dummy:
        dummy_data = gtfs_dummy.create_dummy_data(list(tde.routes),
                                                  list(tde.stops))
        writer.add_trips(dummy_data.trips)
        writer.add_stop_times(dummy_data.stop_times)
        writer.add_calendar(dummy_data.calendar)
        writer.add_shapes(dummy_data.shapes)
        patched_agencies = gtfs_dummy.patch_agencies(tde.agencies)

    if patched_agencies:
        writer.add_agencies(patched_agencies)
    else:
        writer.add_agencies(tde.agencies)
    writer.add_stops(tde.stops)
    writer.add_routes(tde.routes)

    zipfile = '{}.zip'.format(filename)
    print('Writing GTFS feed to %s' % zipfile)
    writer.write_zipped(zipfile)

    return zipfile


if __name__ == '__main__':
    app.run('0.0.0.0', 3000, debug=True)
