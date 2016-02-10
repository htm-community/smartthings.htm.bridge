import os

from influxdb import InfluxDBClient

# This is only necessary for Python < 2.7.9
# import urllib3.contrib.pyopenssl
# urllib3.contrib.pyopenssl.inject_into_urllib3()

INFLUX_HOST = os.environ["INFLUX_HOST"]
INFLUX_PORT = os.environ["INFLUX_PORT"]
INFLUX_USER = os.environ["INFLUX_USER"]
INFLUX_PASS = os.environ["INFLUX_PASS"]
INFLUX_DB = "smartthings_htm_bridge"
INFLUX_SSL = "INFLUX_SSL" in os.environ \
          and os.environ["INFLUX_SSL"] != "" \
          and os.environ["INFLUX_SSL"] != "0" \
          and os.environ["INFLUX_SSL"].lower() != "false" 
print os.environ["INFLUX_SSL"]
print("Connecting to {0}:{1}@{2}:{3} (SSL? {4})".format(
  INFLUX_USER, INFLUX_PASS, INFLUX_HOST, INFLUX_PORT, INFLUX_SSL
))
client = InfluxDBClient(
  host=INFLUX_HOST,
  port=INFLUX_PORT,
  username=INFLUX_USER,
  password=INFLUX_PASS,
  ssl=INFLUX_SSL
)

if INFLUX_DB not in [d["name"] for d in client.get_list_database()]:
  print "Creating Influx database '%s'..." % INFLUX_DB
  client.create_database(INFLUX_DB)

print "Using Influx database '%s'." % INFLUX_DB
client.switch_database(INFLUX_DB)


def saveHtmInference(result, component, measurement, timestamp, timezone):
  print "Saving HTM inference..."
  anomalyScore = result["inferences"]["anomalyScore"]
  anomalyLikelihood = result["anomalyLikelihood"]
  
  payload = [{
    "tags": {
      "component": component,
      "timezone": timezone,
    },
    "time": timestamp,
    "measurement": measurement + '_inference',
    "fields": {
      "anomalyScore": anomalyScore,
      "anomalyLikelihood": anomalyLikelihood
    }
  }]
  
  client.write_points(payload)
  

def saveSensorData(point):
  print "Saving sensor data point..."
  
  timezone = "unknown"
  if "timezone" in point:
    timezone = point["timezone"]
  
  payload = [{
    "tags": {
      "component": point["component"],
      "timezone": timezone,
    },
    "time": point["time"],
    "measurement": point["stream"],
    "fields": {
      "value": float(point["value"]),
    }
  }]
  
  client.write_points(payload)
  

def saveResult(result, point):
  timezone = "unknown"
  if "timezone" in point:
    timezone = point["timezone"]
  saveSensorData(point)
  saveHtmInference(result, point["component"], point["stream"], point["time"], timezone)


def listSensors():
  return client.get_list_series()


def queryMeasurement(measurement, component, limit=None, since=None):
  query = "SELECT * FROM " + measurement \
        + " WHERE component = '" + component + "'"
  if since is not None:
    query += " AND time > {0}s".format(since)
  query += " GROUP BY * ORDER BY time DESC"
  if limit is not None:
    query += " LIMIT {0}".format(limit)
  
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


def getSensorData(measurement, component, limit=None, since=None, sensorOnly=False):
  sensorData = queryMeasurement(measurement, component, limit, since)
  if sensorOnly:
    return sensorData
  
  inferenceData = queryMeasurement(measurement + "_inference", component, limit, since)
  print sensorData
  print 
  print inferenceData



