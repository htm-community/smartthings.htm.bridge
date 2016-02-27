import os
import json

import web

from influxclient import SensorClient

INFLUX_DATABASE = os.environ["INFLUX_DB"]
DEFAULT_PORT = 8080

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
    data = json.loads(web.data())
    sensorClient.saveSensorData(data)
    return json.dumps({"result": "success"})


class SensorList:

  def GET(self):
    return json.dumps(getSensorIds(sensorClient.listSensors()))


class SensorData:

  def GET(self, measurement, component):
    query = web.input(limit=None, since=None, aggregate=None)
    since = query.since
    if since is not None:
      # InfluxDB expects a 19-digit timestamp.
      since = int(query.since) * 1000000000
    sensor = sensorClient.getSensorData(
      measurement,
      component,
      limit=query.limit,
      since=since,
      aggregation=query.aggregate
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
