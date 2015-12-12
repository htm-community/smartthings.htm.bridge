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
  "/_sensors", "sensors",
  "/_sensor/(.+)/(.+)", "sensor",
  "/foshizzle", "charts"
)
app = web.application(urls, globals())
render = web.template.render("templates/")


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


class index:

  def GET(self):
    modelIds = [m["guid"] for m in listModels()]
    return render.layout(
      render.index(modelIds)
    )

  def POST(self):
    data = json.loads(web.data())
    # saveSmartThingDataPoint(data)
    modelIds = [m["guid"] for m in listModels()]
    modelId = data["component"] + '_' +  data["stream"]
    if modelId not in modelIds:
      createModelFromDataPoint(modelId, data)
    htmResult = runOneDataPoint(modelId, data)
    saveResult(htmResult, data)
    return json.dumps({"result": "success"})


class sensors:
  def GET(self):
    sensors = listSensors()
    sensorIds = []
    for sensor in sensors:
      name = sensor["name"]
      for tag in sensor["tags"]:
        sensorIds.append(name + "/" + tag["component"])
    return json.dumps(list(set(sensorIds)))


class sensor:
  def GET(self, measurement, component):
    sensor = getSensorData(measurement, component)
    return json.dumps(sensor.raw)


class charts:
  def GET(self):
    return render.layout(render.charts())


if __name__ == "__main__":
  app.run()
