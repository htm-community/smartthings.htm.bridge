import os

from influxdb import InfluxDBClient

# This is only necessary for Python < 2.7.9
# import urllib3.contrib.pyopenssl
# urllib3.contrib.pyopenssl.inject_into_urllib3()

DEFAULT_HOST = os.environ["INFLUX_HOST"]
DEFAULT_PORT = os.environ["INFLUX_PORT"]
DEFAULT_USER = os.environ["INFLUX_USER"]
DEFAULT_PASS = os.environ["INFLUX_PASS"]
DEFAULT_SSL = "INFLUX_SSL" in os.environ \
              and os.environ["INFLUX_SSL"] != "" \
              and os.environ["INFLUX_SSL"] != "0" \
              and os.environ["INFLUX_SSL"].lower() != "false"


def zipSensorAndInferenceData(sensorData, inferenceData):
  # Validate that they are the same length
  if isinstance(inferenceData, list) or len(sensorData["series"][0]) != len(inferenceData["series"][0]):
    # Just return the sensor data and warn.
    print "WARNING: sensor and inference data arrays were different sizes. Only returning sensor data."
    return sensorData

  sensorSeries = sensorData["series"][0]
  inferenceSeries = inferenceData["series"][0]

  sensorValues = sensorSeries["values"]
  sensorColumns = sensorSeries["columns"]
  inferenceValues = inferenceSeries["values"]
  inferenceColumns = inferenceSeries["columns"]

  columnsOut = sensorColumns + inferenceColumns[1:]
  valuesOut = []

  for i, sensorValue in enumerate(sensorValues):
    valueOut = sensorValue + inferenceValues[i][1:]
    valuesOut.append(valueOut)

  dataOut = {
    "series": [{
      "values": valuesOut,
      "name": sensorSeries["name"],
      "columns": columnsOut,
      "tags": sensorSeries["tags"]
    }]
  }

  return dataOut



class SensorClient(object):

  def __init__(self,
               database,
               host=DEFAULT_HOST,
               port=DEFAULT_PORT,
               username=DEFAULT_USER,
               password=DEFAULT_PASS,
               ssl=DEFAULT_SSL,
               verbose=False
               ):
    self._database = database
    self._verbose = verbose
    if self._verbose:
      print("Connecting to {0}:{1}@{2}:{3} (SSL? {4})".format(
        username, "***********", host, port, ssl
      ))

    self._client = InfluxDBClient(
      host=host,
      port=port,
      username=username,
      password=password,
      ssl=ssl
    )

    # TODO: having IO in the constructor is a bad idea, but this is a prototype.
    if database not in [d["name"] for d in self._client.get_list_database()]:
      print "Creating Influx database '%s'..." % database
      self._client.create_database(database)

    if self._verbose:
      print "Using Influx database '%s'." % database
    self._client.switch_database(database)




  def saveHtmInference(self,
                       result,
                       component,
                       measurement,
                       timestamp,
                       timezone
                       ):
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

    self._client.write_points(payload)


  def saveSensorData(self, point):
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

    self._client.write_points(payload)


  def saveResult(self, result, point):
    timezone = "unknown"
    if "timezone" in point:
      timezone = point["timezone"]
    self.saveSensorData(point)
    self.saveHtmInference(
      result, point["component"], point["stream"], point["time"], timezone
    )


  def listSensors(self):
    allSensors = self._client.get_list_series()
    sensorsOnly = (s for s in allSensors if not s["name"].endswith("_inference"))
    return sensorsOnly


  def queryMeasurement(self,
                       measurement,
                       component,
                       limit=None,
                       since=None):
    query = "SELECT * FROM " + measurement \
          + " WHERE component = '" + component + "'"
    if since is not None:
      query += " AND time > {0}s".format(since)
    query += " GROUP BY * ORDER BY time DESC"
    if limit is not None:
      query += " LIMIT {0}".format(limit)

    response = self._client.query(query)

    # Don't process empty responses
    if len(response) < 1:
      return []

    data = response.raw
    # Because of the descending order in the query, we want to reverse the data so
    # it is actually in ascending order. The descending order was really just to get
    # the latest data.
    data["series"][0]["values"] = list(reversed(data["series"][0]["values"]))
    return data


  def getSensorData(self, measurement, component, limit=None, since=None):
    sensorData = self.queryMeasurement(measurement, component, limit, since)
    inferenceData = self.queryMeasurement(measurement + "_inference", component, limit, since)
    return zipSensorAndInferenceData(sensorData, inferenceData)



