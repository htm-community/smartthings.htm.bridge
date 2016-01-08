import os

from influxdb import InfluxDBClient

# This is only necessary for Python < 2.7.9
# import urllib3.contrib.pyopenssl
# urllib3.contrib.pyopenssl.inject_into_urllib3()

class InfluxDbSensorClient():
  
  def __init__(self, host, port, user, passwd, db, sensorDb, ssl):
    print("Connecting to InfluxDB at {0}:{1}@{2}:{3}".format(
      user, passwd, host, port
    ))
    self.client = InfluxDBClient(
      host=host,
      port=port,
      username=user,
      password=passwd,
      database=db,
      ssl=ssl
    )
    self.backupClient = InfluxDBClient(
      host=host,
      port=port,
      username=user,
      password=passwd,
      database=sensorDb,
      ssl=ssl
    )


  def saveSensorOnly(self, point):
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
    self.backupClient.write_points(payload)
  
  
  def saveResult(self, result, point):
    anomalyScore = None
    anomalyLikelihood = None
  
    if result is not None:
      print "Saving HTM result"
      anomalyScore = result["inferences"]["anomalyScore"]
      anomalyLikelihood = result["anomalyLikelihood"]
  
    print "Saving sensor data point"
  
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
    self.client.write_points(payload)
  
  
  def listSensors(self):
    return self.client.get_list_series()
  
  
  def getSensorData(self, measurement, component, limit=None, since=None):
    query = "SELECT * FROM " + measurement \
          + " WHERE component = '" + component + "'"
    if since is not None:
      query += " AND time > {0}s".format(since)
    query += " GROUP BY * ORDER BY time DESC"
    if limit is not None:
      query += " LIMIT {0}".format(limit)
    response = self.client.query(query)
  
    # Don't process empty responses
    if len(response) < 1:
      return []
  
    data = response.raw
    # Because of the descending order in the query, we want to reverse the data so
    # it is actually in ascending order. The descending order was really just to get
    # the latest data.
    data["series"][0]["values"] = list(reversed(data["series"][0]["values"]))
    return data
  
  
  
