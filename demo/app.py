"""osmtogtfs web app"""
import os
import pathlib
import tempfile
import urllib.parse
import urllib.request

import validators
from flask import Flask, request, send_file, render_template, flash
from werkzeug.utils import secure_filename

from osmtogtfs.cli import main


app = Flask(__name__)
application = app

app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['SECRET_KEY'] = 'super secret string'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method != 'POST':
        return render_template('index.html')

    uploaded_filepath = \
        save_file(request.files['file']) if 'file' in request.files else None
    url = request.form.get('url')

    if not url and not uploaded_filepath:
        flash('Provide a URL or upload a file.')
        return render_template('index.html')

    if not uploaded_filepath and not validators.url(url):
        flash('Not a valid URL.')
        return render_template('index.html')

    filename = uploaded_filepath or dl_osm(url)
    zipfile = create_zipfeed(filename, bool(request.form.get('dummy')))

    return send_file(
        zipfile,
        attachment_filename=pathlib.Path(zipfile).name,
        as_attachment=True)


def save_file(file):
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath


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
