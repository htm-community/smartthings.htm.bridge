import os
import json

import web

from influxhtm import InfluxHtmClient

INFLUX_DATABASE = os.environ["INFLUX_DB"]
DEFAULT_PORT = 8080

ihtmClient = InfluxHtmClient(INFLUX_DATABASE, verbose=True)


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
    data = json.loads(web.data())
    # {u'component': u'Keurig', u'stream': u'power', u'value': 6642, u'time': u'2016-03-10 22:24:34.000'}
    measurement = data["stream"]
    component = data["component"]
    sensor = ihtmClient.getSensor(
      measurement=measurement, component=component
    )
    if sensor is None:
      sensor = ihtmClient.createSensor(
        measurement=measurement, component=component
      )
    sensor.write({
      "time": data["time"],
      "value": data["value"]
    })
    return json.dumps({"result": "success"})


class SensorList:

  def GET(self):
    sensorIds = [
      "{}/{}".format(s.getMeasurement(), s.getComponent())
      for s in ihtmClient.getSensors()]
    return json.dumps(sensorIds)


class SensorData:

  def GET(self, measurement, component):
    query = web.input(limit=None, since=None, aggregate=None)
    print query
    since = query.since
    if since is not None:
      # InfluxDB expects a 19-digit timestamp.
      since = int(query.since) * 1000000000
    sensor = ihtmClient.getSensor(measurement=measurement, component=component)
    data = sensor.getCombinedSensorData(
      limit=query.limit,
      since=since,
      aggregation=query.aggregate
    )
    return json.dumps(data)


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
