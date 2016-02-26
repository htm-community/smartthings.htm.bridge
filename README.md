# smartthings.htm.bridge

> ## Work in Progress

A bridge for smartthings apps to post data to, which will in turn run data through HTM REST API.

## To Install

    python setup.py install [--user]

You must have the following env vars:

```bash
INFLUX_HOST=localhost
INFLUX_PORT=8086
INFLUX_USER=username
INFLUX_PASS=password
INFLUX_DB=database_name
INFLUX_SSL=1
```

## To Run Data Server

    cd st_htm_bridge/server && python server.py

## Command Line Interface

You can use this to interact with HITC. I use it to manage models and view sensor data. Here's what it can do.

### Models

#### Create a model

    ./cli.py models:create \
        --guid=<guid> \
        --paramPath=<path-to-params-json>

#### List models

    ./cli.py models:list

#### Delete a model

    ./cli.py models:delete \
        --guid=<guid>

#### Delete all models

    ./cli.py models:deleteAll

#### Run data through a model

    ./cli.py models:loadData \
        --component=<component> \
        --measurement=<measurement> \
        --limit=<limit> \
        --guid=<guid>

## Sensor Data

#### List available sensors

    ./cli.py sensors:list


#### List data available for a sensor

    ./cli.py sensors:data \
        --component=<component> \
        --measurement=<measurement> \
        --limit=<limit>

#### List HTM inferences available for a sensor

    ./cli.py sensors:inference \
        --component=<component> \
        --measurement=<measurement> \
        --limit=<limit>

#### Transfer sensor data from one DB to another

    ./cli.py sensors:transfer \
        --from=<fromDB> \
        --to=<toDb> \
        --measurement=<measurement> \
        --component=<component> \
        --limit=<limit>
