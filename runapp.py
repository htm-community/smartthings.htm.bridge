import json
import time
from datetime import datetime
import urllib

import web

from persist import saveSmartThingDataPoint
from htmclient import listModels, createModel, sendData

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

urls = (
  "/", "index"
)
app = web.application(urls, globals())
render = web.template.render("templates/")


def createModelFromDataPoint(point):
  guid = urllib.quote_plus(point["component"])
  with open("anomaly_params.json") as inputParams:
    modelSpec = json.loads(inputParams.read())
  modelSpec["guid"] = guid
  createdModel = createModel(json.dumps(modelSpec))
  print "Created {0}".format(createdModel)


def runOneDataPoint(point):
  print point
  modelId = point["component"]
  timeString = point["time"]
  timestamp = int(time.mktime(datetime.strptime(timeString, DATE_FORMAT).timetuple()))
  dataRow = {
    "c0": timestamp,
    "c1": point["value"]
  }
  result = sendData(modelId, dataRow)
  print result


class index:

  def GET(self):
    modelIds = [m["guid"] for m in listModels()]
    return render.layout(
      render.index(modelIds)
    )

  def POST(self):
    data = json.loads(web.data())
    saveSmartThingDataPoint(data)
    modelIds = [m["guid"] for m in listModels()]
    if data["component"] not in modelIds:
      createModelFromDataPoint(data)
    else:
      runOneDataPoint(data)
    return json.dumps({"result": "success"})



if __name__ == "__main__":
  app.run()