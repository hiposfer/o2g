# osmtogtfs

[![Build Status](https://travis-ci.org/hiposfer/osmtogtfs.svg?branch=master)](https://travis-ci.org/hiposfer/osmtogtfs) [![pypi](https://img.shields.io/pypi/v/osmtogtfs.svg)](https://pypi.python.org/pypi/osmtogtfs)

Extracts partial GTFS feed from OSM data.

OpenStreeMaps data contain information about bus, tram, train and other public transport means.
This information is not enought for providing a complete routing service, most importantly because
it lacks timing data. However, it still contains routes, stop positions and some other useful data.

This tool takes an OSM file or URI and thanks to [osmium](http://osmcode.org/) library converts it to a partial 
[GTFS](https://developers.google.com/transit/gtfs/reference/) feed. GTFS is the de facto standard 
for sharing public transport information and there are many tools around it. The resulting feed would
not validate if you check it, because it is of course partial. Nevertheless, it is yet valuable to us.

## Installation
This tool uses osmium which is a C++ library built using boost, so one should install that first.
The best way would be using the package manager of your OS and installing [pyosmium](https://github.com/osmcode/pyosmium).

Afterwards install the script from pypi:

    $ pip install osmtogtfs

Alternatively you can clone the repo and install it:

    $ git clone https://github.com/hiposfer/osmtogtfs & cd osmtogtfs
    $ python3 setup.py install

This will install `osmtogtfs` command and its alias `o2g` on your system. Alternatively, you can run `osmtogtfs/cli.py`.

Make sure to run these commands with python 3.

## Usage
Run the tool over your OSM data source (or whatever osmium accepts):

    osmtogtfs <osmfile>

After a while, depending on the file size, a file named `gtfs.zip` will be produced inside the working directory.
Moreover, if you install the package, you will get an script called `osmtogtfs` in your python path:

    $ osmtogtfs --help
    Usage: osmtogtfs [OPTIONS] INPUT

    Options:
      --outdir PATH   Store output in this directory.
      --zipfile PATH  Save as Zip file if provided.
      --loglevel      Set the logging level.
      --help          Show this message and exit.

`--outdir` defaults to the working directory and if `--zipfile` is provided, the feed will be zipped and stored in
the _outdir_ with the given name, otherwise feed will be stored as plain text in multiple files.

### Web Demo
There is a small web app inside `demo` folder. It accepts a URL to a osmium supported file. It will then convert it
to a zipped GTFS feed. You will need `pipenv` command to install and run it:

    $ cd demo
    $ pip install pipenv
    $ pipenv install
    $ python3 app.py

Browse to [http://localhost:3000](http://localhost:3000) afterwards to use it.

This demo is also running at [http://o2g.hiposfer.com](http://o2g.hiposfer.com). It is possible to directly download a zipped GTFS feed for a given OSM URL too:

    http 'http://o2g.hiposfer.com/o2g?url=http://download.geofabrik.de/europe/liechtenstein-latest.osm.bz2' > gtfs.zip

The above command uses the [HTTPie](https://httpie.org/) tool.

### With Docker
If osmium is not available in your package manager, it could be troublesome to install it manually. So here
is a docker image that could be used directly:

    $ docker run -it -p 3000:3000 hiposfer/osmtogtfs

Then browse to [http://localhost:3000](http://localhost:3000).

## Development
We use `pipenv` to manage dependencies and virtualenvs. Install and activate it before anything:

    $ cd osmtogtfs
    $ pip install pipenv
    $ pipenv install
    $ pipenv shell

The last command will give us a shell within the newly created virtualenv.

In order to update the `requirements.txt` we simply use `pipenv`:

    $ pipenv run pip freeze > requirements.txt

### Tests
We use the `pytest` package for testing. If you have followed above instructions, `pytest` should be
already installed. Otherwise install pytest and run the tests:

    $ pip install pytest
    $ pytest -s

`-s` disables capturing and shows us more output (such as print statements and log messages).

### Profiling
In order to profile the code we use `cProfile`:
    
    # For the `osmtogtfs` script
    $ python -m cProfile -s cumtime osmtogtfs/cli.py resources/osm/bremen-latest.osm.pbf --outdir output/bremen --dummy > output/benchmarks/bremen.txt
    $ python -m cProfile -s cumtime osmtogtfs/cli.py resources/osm/saarland-latest.osm.pbf --outdir output/saarland --dummy > output/benchmarks/saarland.txt

You will find the result in [`output/benchmark.txt`](output/benchmark.txt).
Theses results are produced on an Archlinux machine with an Intel(R) Core(TM) i5-3210M CPU @ 2.50GHz CPU with 16GB RAM.

### Dummy Feed Information
Not all of GTFS necessary data are available in OSM files. In order to fill the missing fields with
some dummy data use `--dummy` CLI option. This will produce `trips.txt`, `stop_times.txt` and `calendar`
feeds. These files will contain dummy data of course.

## Implementation Notes
In this section we describe important aspects of the implementation in order to help understand how the program works.

### Field Mapping
GTFS feeds could contain up to thirteen different CSV files with `.txt` extension. Six of these files are required for a valid
feed, including _agency.txt_, _stops.txt_, _routes.txt_, _trips.txt_, _stop_times.txt_ and _calendar.txt_. 
Each file contains a set of comumns. Some columns are required and some are optional. 
Most importantly, not all the fields necessary to build a GTFS feed are available in OSM data. 
Therefore we have to generate some fileds ourselves or leave them blank.
Below we cover how the values for each column of the files that we produce at the moment are produced.

#### agency.txt
We use _operator_ tag on OSM relations which are tagged as `relation=route` to extract agency information. 
However, there are some routes without operator tags. In such cases we use a dummy agency:

    {'agency_id': -1, 'agency_name': 'Unkown agency', 'agency_timezone': ''}

 - agency_id: we use the _operator_ value to produce the _agency_id_: `agency_id = int(hashlib.sha256(op_name.encode('utf-8')).hexdigest(), 16) % 10**8`
 - agency_name: the value of the _operator_ tag
 - agency_timezone: we guess it based on the coordinates of the elements in the relation

#### stops.txt

 - stop_id: value of the node id from OSM
 - stop_name: value of _name_ tag or _Unknown_
 - stop_lon: longitute of the node
 - stop_lat: latitute of the node

#### routes.txt

 - route_id: id of the OSM relation element
 - route_short_name: value of _name_ or _ref_ tag of the relation
 - route_long_name: a combination of _from_ and _to_ tags on the relation otherwise empty
 - route_type: we map OSM route types to GTFS
 - route_url: link to the relation on openstreetmaps.org
 - route_color: value of the _color_ tag if present otherwise empty
 - agency_id: ID of the agency otherwise -1

### OSM to GTFS Route Type Mapping
 Below is the mapping that we use, the left column is the OSM value and the right column is the 
 corresponding value from GTFS specification (make sure the see the code for any changes):

    tram: 		0
    light_rail: 0
    subway: 	1
    rail: 		2
    railway: 	2
    train: 		2
    bus: 		3
    ex-bus: 	3
    ferry: 		4
    cableCar: 	5
    gondola: 	6
    funicular: 	7


### namedtuples as the preferred data structure
In order to decrease the necessary memory, we use mostly namedtuples (which are basically tuples) to store data.


## Lincense
MIT
