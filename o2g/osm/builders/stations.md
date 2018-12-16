Notes on Stations
-----------------

Station is a node with "public_transport:station" and "railway:station" tags. could appear in different relations as "stop", "halt" or a simple member node. Stations appear in GTFS stops.txt as parent_stop of other stops. This information will be used to produce "transfers" in trip planning. That's why we need to process them correctly.

Station node is member of a route relation as "stop". In this case it has "public_transport:station" and "railway:station" tags.

Station node is member of a route relation with no relation type. It is just a member. Tags are like the first case.

(hint: other members have "railway:stop" or "railway:platform" tags.)

As an example see Freiburg Hbf. [Station node](https://www.openstreetmap.org/node/21769883) appears in many relations as "stop", "halt" or without membership type. It has "public_transport:staion" and "railway:stop" tags. In [this relation (Freiburg Hbf))](https://www.openstreetmap.org/relation/6311483) it appears as a member node with no type, however in [this one)[https://www.openstreetmap.org/relation/4573043] it appears as a "stop" and in [this one](https://www.openstreetmap.org/relation/70678) as a "halt".


Stations, Stop Areas and Stops
------------------------------
When we come across stop_area relations, we have to make sure there is one station for that stop_area or we have to create one (in case the station node is missing in OSM or is not linked to any stop_area). For each stop in the stop_are we have to set the correct parent_station, which would be another stop in GTFS jargon.


Bus Stations
------------
Bus stations are often defined as stop_areas. So far I have not found any station nodes for bus stations. For example see [Freiburg ZOB](https://www.openstreetmap.org/node/251365749). The node is there but it has no public_transport tags. So we have to calculate one when we are processing the [ZOB stop_are](https://www.openstreetmap.org/relation/7159172#map=19/47.99645/7.84104).

TODO
----
"terminal" membership types
"halt" membership types
amenity=bus_station
highway=bus_stop
https://wiki.openstreetmap.org/wiki/Tag:amenity=bus_station

Idea for missing station nodes
------------------------------
If there is no node for a stop_area tagged as station or amenity=bus_station, we have to either calculate or edit the OSM. Editing OSM is a better approach, since we contribute back to OSM and also it takes less computing power. Otherwise we have to go through all stop_area members and try to guess/calculate the position.

For the time being we can simply produce warnings for such cases.

