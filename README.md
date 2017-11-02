# osmtogtfs [![Build Status](https://travis-ci.org/hiposfer/osmtogtfs.svg?branch=master)](https://travis-ci.org/hiposfer/osmtogtfs)
Extracts partial GTFS feed from OSM data.

OpenStreeMaps data contain information about bus, tram, train and other public transport means.
This information is not enought for providing a complete routing service, most importantly because
it lacks timing data. However, it still contains routes, stop positions and some other useful data.

This tool takes an OSM file or URI and thanks to [osmium](http://osmcode.org/) library converts it to a partial 
[GTFS](https://developers.google.com/transit/gtfs/reference/) feed. GTFS is the de facto standard 
for sharing public transport information and there are many tools around it. The resulting feed would
not validate if you check it, because it is of course partial. Nevertheless, it is yet valuable to us.

# Installation
This tool uses osmium which is a C++ library built using boost, so one should install that first.
The best way would be using the package manager of your OS and installing [pyosmium](https://github.com/osmcode/pyosmium).
Afterwards clone the repo and install it:

    $ git clone https://github.com/hiposfer/osmtogtfs & cd osmtogtfs
    $ python setup.py install


This will install `osmtogtfs.py` executable on your OS. You can also directly run the script found
in the source code. Make sure to run it with python 3.

# Tests
We use wonder `pytest` package for testing. Install pytest and run the tests:

    $ pip install pytest
    $ pytest -s tests/tests.py

`-s` disables capturing and shows us more output (such as print statements and log messages).

## Pytest Caching
In order to run tests faster we use caching. The result of OSM preprocessing will be cached and used
for subsequent tests. In order to clear the cache run pytest with `--cache-clear` option.

# Usage
Run the tool over your OSM data source (or whatever osmium accepts):

    python osmtogtfs.py <osmfile>

After a while, depending on the file size, a file named `gtfs.zip` will be produced inside the working directory.


# Lincense
MIT
