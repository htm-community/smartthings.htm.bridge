import json
import time
from datetime import datetime
import urllib

import web

from persist import saveSmartThingDataPoint, saveHtmResult
from htmclient import listModels, createModel, sendData

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# 2015-12-08 23:12:47.105

urls = (
  "/", "index"
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
    saveSmartThingDataPoint(data)
    modelIds = [m["guid"] for m in listModels()]
    modelId = data["component"]
    print "Existing models:"
    print modelIds
    print "current model id:"
    print modelId
    if modelId not in modelIds:
      print "creating new one"
      createModelFromDataPoint(modelId, data)
    else:
      print "running data through existing model"
      htmResult = runOneDataPoint(modelId, data)
      saveHtmResult(htmResult, data)
    return json.dumps({"result": "success"})



if __name__ == "__main__":
  app.run()