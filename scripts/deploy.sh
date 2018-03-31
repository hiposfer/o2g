#!/bin/bash
docker login -u _ -p "$HEROKU_TOKEN"  registry.heroku.com
docker build -t registry.heroku.com/o2g/web .
docker push registry.heroku.com/o2g/web
