import os
import json
import time
from datetime import datetime

import web
from hitcpy import HITC

from influxclient import saveResult, listSensors, getSensorData


DEFAULT_PORT = 8080
DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105


#####################
# Utility functions #
#####################

def getHitcUrl():
  if "HITC" not in os.environ:
    return None
  url = os.environ["HITC"]
  if url.endswith("/"):
    url = url[:-1]
  return url


def runOneDataPoint(hitcClient, modelId, point):
  timeString = point["time"]
  timestamp = int(time.mktime(datetime.strptime(timeString, DATE_FORMAT).timetuple()))
  dataRow = {
    "c0": timestamp,
    "c1": point["value"]
  }
  # There is only one value in the result list, so pop() it off.
  return hitcClient.get_model(modelId).run(dataRow).pop()


def getHitcClient():
  hitcClient = None
  hitcUrl = getHitcUrl()
  if hitcUrl is not None:
    hitcClient = HITC(hitcUrl)
  return hitcClient


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

urls = (
  '/', 'Index',
  '/_models/?', 'Models',
  '/_data/sensors/?', 'SensorList',
  '/_data/sensor/(.+)/(.+)/?', 'SensorData'
)

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
      htmResult = runOneDataPoint(hitcClient, modelId, data)
      saveResult(htmResult, data)
    else:
      saveResult(None, data)
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
    print "hello"
    return json.dumps(getSensorIds(listSensors()))


class SensorData:

  def GET(self, measurement, component):
    query = web.input(limit=None, since=None)
    sensor = getSensorData(
      measurement,
      component,
      limit=query.limit,
      since=query.since
    )
    return json.dumps(sensor)


##############
# Start here #
##############

if __name__ == "__main__":
  port = DEFAULT_PORT
  if "PORT" in os.environ:
    port = int(os.environ["PORT"])
  debug = False
  if "DEBUG" in os.environ:
    debug = True

  print "RUNNING WEBPY APP on port %s" % port
  app = web.application(urls, globals())
  app.run()
