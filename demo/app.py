"""osmtogtfs web app"""
import os
import pathlib
import tempfile
import urllib.parse
import urllib.request

import validators
from flask import Flask, request, send_file, render_template

from osmtogtfs.cli import main


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
    zipfile = '{}.zip'.format(filename)
    print('Writing GTFS feed to %s' % zipfile)
    main(filename, '.', zipfile, dummy)
    return zipfile


if __name__ == '__main__':
    app.run('0.0.0.0', int(os.getenv('PORT', 3000)), debug=True)
