import os
import json

import web

from influxclient import SensorClient
from utils import getHitcClient, runOneDataPoint

INFLUX_DATABASE = os.environ["INFLUX_DB"]
DEFAULT_PORT = 8080
DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

sensorClient = SensorClient(INFLUX_DATABASE, verbose=True)


#################
# HTTP Handlers #
#################

urls = (
  '/', 'Index',
  '/_models/?', 'Models',
  '/_data/sensors/?', 'SensorList',
  '/_data/sensor/(.+)/(.+)/?', 'SensorData'
)


def getSensorIds(sensors):
  sensorIds = []
  for sensor in sensors:
    name = sensor["name"]
    for tag in sensor["tags"]:
      sensorIds.append(name + "/" + tag["component"])
  return sorted(list(set(sensorIds)))


class Index:

  def GET(self):
    """
    Handles GET calls to "/", which displays HTML.
    Handles POST data calls to "/", which saves off sensor data.
    """
    raise web.seeother("/static/index.html")

  def POST(self):
    """
    Handles GET calls to "/", which displays HTML.
    Handles POST data calls to "/", which saves off sensor data.
    """
    hitcClient = getHitcClient()
    data = json.loads(web.data())
    if hitcClient is not None:
      modelIds = [m.guid for m in hitcClient.get_all_models()]
      modelId = data["component"] + '_' +  data["stream"]
      if modelId not in modelIds:
        with open("anomaly_params.json") as inputParams:
          modelSpec = json.loads(inputParams.read())
          modelSpec["guid"] = modelId
          hitcClient.create_model(modelSpec)
      htmResult = runOneDataPoint(
        hitcClient, modelId, data["time"], data["value"]
      )
      sensorClient.saveResult(htmResult, data)
    else:
      sensorClient.saveResult(None, data)
    return json.dumps({"result": "success"})


class Models:

  def GET(self):
    hitcClient = getHitcClient()
    if hitcClient is not None:
      modelIds = [m.guid for m in hitcClient.get_all_models()]
    else:
      modelIds = []
    return json.dumps(modelIds)


class SensorList:

  def GET(self):
    return json.dumps(getSensorIds(sensorClient.listSensors()))


class SensorData:

  def GET(self, measurement, component):
    query = web.input(limit=None, since=None, aggregate=None)
    sensor = sensorClient.getSensorData(
      measurement,
      component,
      limit=query.limit,
      since=query.since,
      aggregate=query.aggregate
    )
    return json.dumps(sensor)


##############
# Start here #
##############

def start():
  port = DEFAULT_PORT
  if "PORT" in os.environ:
    port = int(os.environ["PORT"])

  print "RUNNING WEBPY APP on port %s" % port
  app = web.application(urls, globals())
  app.run()


if __name__ == "__main__":
  start()
