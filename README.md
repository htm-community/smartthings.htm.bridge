# smartthings.htm.bridge

> ## Work in Progress

The goal of this project is to create a platform for storing SmartThings sensor data into a time-series database, allowing experimentation with HTM models.

There are currently two components to this application:

1. Web Server: Accepts POST data from [HTTP Poster SmartApp](https://github.com/rhyolight/smartthings-apps/blob/master/http-poster.groovy) and saves raw data into InfluxDB. Displays saved data in graphs that users can aggregate and navigate.
1. Command Line Interface: Allows users to experiment with the stored raw IoT data with HTM via [HITC](https://github.com/nupic-community/hitc).

The web server currently works. The CLI is still under construction. 

## To Install

    python setup.py install [--user]

You must have the following env vars:

```bash
INFLUX_HOST=localhost
INFLUX_PORT=8086
INFLUX_USER=username
INFLUX_PASS=password
INFLUX_DB=database_name
INFLUX_SSL=1 # whether to use SSL or not when connecting
```

## To Run Web Server

    cd st_htm_bridge/data && python server.py
    
The open <http://localhost:8080/> in your browser.

## Command Line Interface

You can use this to interact with InfluxDB and [HITC](https://github.com/nupic-community/hitc). I use it to manage models and view sensor data. Here's what it can do.

### Models

The commands below deal with HTM models used to analyze the SmartThings sensor data.

#### Create a model

    st_htm_bridge_cli models:create \
        --guid=<guid> [optional] \
        --paramPath=<path-to-params-json>

#### List models

    st_htm_bridge_cli models:list

#### Delete a model

    st_htm_bridge_cli models:delete \
        --guid=<guid>

#### Delete all models

    st_htm_bridge_cli models:deleteAll

#### Feed a model data

The `--aggregation` option can be a time string like `1s`, `5m`, `2w`, etc.

    st_htm_bridge_cli models:load \
        --guid=<guid>
        --component=<component> \
        --measurement=<measurement> \
        --aggregation=<aggregation> [optional]
        --limit=<limit> [optional]

Functionality here should be able to choose aggregation options for InfluxDB and feed data directly into a newly created HTM model or an existing model.

## Sensor Data

The commands below query raw InfluxDB sensor data from SmartThings.

#### List available sensors

    st_htm_bridge_cli sensors:list

#### List data available for a sensor

    st_htm_bridge_cli sensors:data \
        --component=<component> \
        --measurement=<measurement> \
        --limit=<limit> [optional]

#### List HTM inferences available for a sensor

    st_htm_bridge_cli sensors:inference \
        --component=<component> \
        --measurement=<measurement> \
        --limit=<limit> [optional]

#### Transfer sensor data from one DB to another

    st_htm_bridge_cli sensors:transfer \
        --from=<fromDB> \
        --to=<toDb> \
        --measurement=<measurement> \
        --component=<component> \
        --limit=<limit> [optional]

#### Delete sensor data

Deletes all data points for specified measurement / component.

    st_htm_bridge_cli sensors:delete \
        --measurement=<measurement> \
        --component=<component>
