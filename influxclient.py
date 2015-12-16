import os

from influxdb import InfluxDBClient

# This is only necessary for Python < 2.7.9
# import urllib3.contrib.pyopenssl
# urllib3.contrib.pyopenssl.inject_into_urllib3()

INFLUX_HOST = os.environ["INFLUX_HOST"]
INFLUX_PORT = os.environ["INFLUX_PORT"]
INFLUX_USER = 'numenta' #os.environ["INFLUX_USER"]
INFLUX_PASS = 'PWXucoyNe7n8' #os.environ["INFLUX_PASS"]
INFLUX_DB = "smartthings"
INFLUX_DB_BACKUP = "smartthings_sensor_only"

print("Connecting to {0}:{1}@{2}:{3}".format(
  INFLUX_USER, INFLUX_PASS, INFLUX_HOST, INFLUX_PORT
))
client = InfluxDBClient(
  host=INFLUX_HOST, 
  port=INFLUX_PORT, 
  username=INFLUX_USER, 
  password=INFLUX_PASS, 
  database=INFLUX_DB,
  ssl=True
)
backupClient = InfluxDBClient(
  host=INFLUX_HOST, 
  port=INFLUX_PORT, 
  username=INFLUX_USER, 
  password=INFLUX_PASS, 
  database=INFLUX_DB_BACKUP,
  ssl=True
)


def saveSensorOnly(point):
  print "Saving sensor only data..."
  timezone = "unknown"
  if "timezone" in point:
    timezone = point["timezone"]

  payload = [{
    "tags": {
      "component": point["component"],
      "timezone": timezone
    },
    "time": point["time"],
    "measurement": point["stream"],
    "fields": {
      "value": float(point["value"])
    }
  }]
  backupClient.write_points(payload)


def saveResult(result, point):
  print "Saving data and HTM result"
  anomalyScore = result["inferences"]["anomalyScore"]
  anomalyLikelihood = result["anomalyLikelihood"]

  timezone = "unknown"
  if "timezone" in point:
    timezone = point["timezone"]

  payload = [{
    "tags": {
      "component": point["component"],
      "timezone": timezone
    },
    "time": point["time"],
    "measurement": point["stream"],
    "fields": {
      "value": float(point["value"]),
      "anomalyScore": anomalyScore,
      "anomalyLikelihood": anomalyLikelihood
    }
  }]

  saveSensorOnly(point)
  client.write_points(payload)


def listSensors():
  return client.get_list_series()


def getSensorData(measurement, component, limit=None, since=None):
  query = "SELECT * FROM " + measurement \
        + " WHERE component = '" + component + "'"
  if since is not None:
    query += " AND time > {0}s".format(since)
  if limit is not None:
    query += " GROUP BY * ORDER BY time DESC LIMIT {0}".format(limit)
  response = client.query(query)

  # Don't process empty responses
  if len(response) < 1:
    return []

  data = response.raw
  # Because of the descending order in the query, we want to reverse the data so
  # it is actually in ascending order. The descending order was really just to get
  # the latest data.
  data["series"][0]["values"] = list(reversed(data["series"][0]["values"]))
  return data



