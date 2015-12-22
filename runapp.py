import os
import json
import time
from datetime import datetime

from hitcpy import HITC

import web

from influxclient import saveResult, listSensors, getSensorData


DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

HITC_URL = os.environ["HITC"]

urls = (
  "/", "Index",
  "/_data/sensors", "SensorsData",
  "/_data/sensor/(.+)/(.+)", "SensorData",
  "/sensors", "Sensors",
  "/sensor/(.+)", "Sensor"
)
app = web.application(urls, globals())
render = web.template.render("templates/")
hitcClient = HITC(HITC_URL)

# Utility functions

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


# HTTP Handlers

class Index:

  def GET(self):
    modelIds = [m.guid for m in hitcClient.get_all_models()]
    return render.layout(
      render.index(modelIds)
    )

  def POST(self):
    data = json.loads(web.data())
    modelIds = [m.guid for m in hitcClient.get_all_models()]
    modelId = data["component"] + '_' +  data["stream"]
    if modelId not in modelIds:
      createModelFromDataPoint(modelId, data)
    htmResult = runOneDataPoint(modelId, data)
    saveResult(htmResult, data)
    return json.dumps({"result": "success"})


class SensorData:

  def GET(self, measurement, component):
    limit = None
    since = None
    query = web.input()
    if "limit" in query:
      limit = query["limit"]
    if "since" in query:
      since = query["since"]
    sensor = getSensorData(measurement, component, limit=limit, since=since)
    return json.dumps(sensor)


class SensorsData:

  def GET(self):
    return json.dumps(getSensorIds(listSensors()))


class Sensors:

  def GET(self):
    # .replace('/', '_').replace(/\+/g, '-')
    sensorIds = [
      s.replace("/", "_").replace("+", "-") 
      for s in getSensorIds(listSensors())
    ]
    return render.layout(
      render.sensors(sensorIds, render.chart)
    )


class Sensor:

  def GET(self, sensor):
    return render.layout(
      render.sensors([sensor], render.chart)
    )



# Start here

if __name__ == "__main__":
  app.run()
