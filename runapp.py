import json
import time
from datetime import datetime
import urllib

import web

from influxclient import saveResult, listSensors, getSensorData
from htmclient import listModels, createModel, sendData

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

urls = (
  "/", "index",
  "/_data/sensors", "sensors",
  "/_data/sensor/(.+)/(.+)", "sensor",
  "/charts", "charts",
  "/chart/(.+)", "chart"
)
app = web.application(urls, globals())
render = web.template.render("templates/")

# Utility functions

def createModelFromDataPoint(modelId, point):
  with open("anomaly_params.json") as inputParams:
    modelSpec = json.loads(inputParams.read())
  modelSpec["guid"] = modelId
  createdModel = createModel(json.dumps(modelSpec))
  print "Created {0}".format(createdModel)


def runOneDataPoint(modelId, point):
  timeString = point["time"]
  timestamp = int(time.mktime(datetime.strptime(timeString, DATE_FORMAT).timetuple()))
  dataRow = {
    "c0": timestamp,
    "c1": point["value"]
  }
  return sendData(modelId, dataRow)


def getSensorIds(sensors):
  sensorIds = []
  for sensor in sensors:
    name = sensor["name"]
    for tag in sensor["tags"]:
      sensorIds.append(name + "/" + tag["component"])
  return sorted(list(set(sensorIds)))


# HTTP Handlers

class index:

  def GET(self):
    modelIds = [m["guid"] for m in listModels()]
    return render.layout(
      render.index(modelIds)
    )

  def POST(self):
    data = json.loads(web.data())
    modelIds = [m["guid"] for m in listModels()]
    modelId = data["component"] + '_' +  data["stream"]
    if modelId not in modelIds:
      createModelFromDataPoint(modelId, data)
    htmResult = runOneDataPoint(modelId, data)
    saveResult(htmResult, data)
    return json.dumps({"result": "success"})


class sensor:

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


class sensors:

  def GET(self):
    return json.dumps(getSensorIds(listSensors()))


class charts:

  def GET(self):
    # .replace('/', '_').replace(/\+/g, '-')
    sensorIds = [
      s.replace("/", "_").replace("+", "-") 
      for s in getSensorIds(listSensors())
    ]
    return render.layout(render.charts(sensorIds))


class chart:

  def GET(self, sensor):
    return render.layout(render.chart(sensor))



# Start here

if __name__ == "__main__":
  app.run()
