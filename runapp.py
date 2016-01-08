import sys
import os
import json
import time
from datetime import datetime

from optparse import OptionParser

from hitcpy import HITC

from flask import Flask, url_for, redirect, request

from influxclient import InfluxDbSensorClient


DEFAULT_PORT = 8080
DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

# HTM In The Cloud Client is declared here because there is an option NOT to use
# it at all, so it could be None.
global hitcClient
global influxClient

app = Flask(__name__)

#####################
# Utility functions #
#####################

def getHitcUrl():
  url = os.environ["HITC"]
  if url.endswith("/"):
    url = url[:-1]
  return url


def createOptionsParser():
  # Options parsing.
  parser = OptionParser(
    usage="%prog [options]\n\n"
          """
  This is a web server that accepts sensor data posted via HTTP and:
    - stores it into an InfluxDB
    - optionally passes it into HTM via HITC
    - displays charts of the data over time
          """
  )
  parser.add_option(
    "-t",
    "--disable-htm",
    action="store_true",
    default=False,
    dest="htmDisabled",
    help="Disable passing all data through HTM server.")
  parser.add_option(
    "-s",
    "--ssl",
    action="store_true",
    default=False,
    dest="ssl",
    help="Connect to InfluxDB with SSL.")
  parser.add_option(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    dest="debug",
    help="Starts server in debug mode.")
  parser.add_option(
    "-p",
    "--port",
    type="int",
    default=DEFAULT_PORT,
    dest="port",
    help="Port to run server on.")
  return parser


def createModelFromDataPoint(modelId, point):
  with open("anomaly_params.json") as inputParams:
    modelSpec = json.loads(inputParams.read())
  modelSpec["guid"] = modelId
  createdModel = hitcClient.create_model(modelSpec)
  print "Created {0}".format(createdModel)


def runOneDataPoint(modelId, point):
  timeString = point["time"]
  timestamp = int(time.mktime(datetime.strptime(timeString, DATE_FORMAT).timetuple()))
  dataRow = {
    "c0": timestamp,
    "c1": point["value"]
  }
  # There is only one value in the result list, so pop() it off.
  return hitcClient.get_model(modelId).run(dataRow).pop()


def getSensorIds(sensors):
  sensorIds = []
  for sensor in sensors:
    name = sensor["name"]
    for tag in sensor["tags"]:
      sensorIds.append(name + "/" + tag["component"])
  return sorted(list(set(sensorIds)))


#################
# HTTP Handlers #
#################

@app.route("/", methods=["GET", "POST"])
def index():
  """
  Handles GET calls to "/", which displays HTML.
  Handles POST data calls to "/", which saves off sensor data.
  """
  global hitcClient
  if request.method == "GET":
    return redirect(url_for("static", filename="index.html"))
  else:
    data = request.json
    if hitcClient is not None:
      modelIds = [m.guid for m in hitcClient.get_all_models()]
      modelId = data["component"] + '_' +  data["stream"]
      if modelId not in modelIds:
        createModelFromDataPoint(modelId, data)
      htmResult = runOneDataPoint(modelId, data)
      influxClient.saveResult(htmResult, data)
    else:
      influxClient.saveResult(None, data)
    return json.dumps({"result": "success"})


@app.route("/_models", methods=["GET"])
def models():
  global hitcClient
  if hitcClient is not None:
    modelIds = [m.guid for m in hitcClient.get_all_models()]
  else:
    modelIds = []
  return json.dumps(modelIds)


@app.route("/_data/sensors", methods=["GET"])
def getSensorList():
  return json.dumps(getSensorIds(influxClient.listSensors()))


@app.route("/_data/sensor/<measurement>/<component>", methods=["GET"])
def getSensorData(measurement, component):
  query = request.args
  sensor = influxClient.getSensorData(
    measurement,
    component,
    limit=query.get("limit"),
    since=query.get("since")
  )
  return json.dumps(sensor)

##############
# Start here #
##############

if __name__ == "__main__":
  global hitcClient
  parser = createOptionsParser()
  (options, args) = parser.parse_args(sys.argv[1:])
  print options
  if options.htmDisabled:
    print "HTM IS DISABLED!"
    hitcClient = None
  else:
    hitcClient = HITC(getHitcUrl())

  host = os.environ["INFLUX_HOST"]
  port = os.environ["INFLUX_PORT"]
  user = os.environ["INFLUX_USER"]
  passwd = os.environ["INFLUX_PASS"]
  db = "smartthings"
  sensorDb = "smartthings_sensor_only"
  influxClient = InfluxDbSensorClient(host, port, user, passwd, db, sensorDb, options.ssl)

  app.run(debug=options.debug, port=options.port)
