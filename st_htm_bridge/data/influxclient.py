import os

from influxdb import InfluxDBClient
import iso8601

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

  # If inferenceData is empty, just return sensorData
  if isinstance(inferenceData, list):
    # Just return the sensor data and warn.
    print "WARNING: No HTM inference data available. Only returning sensor data."
    return sensorData

  sensorSeries = sensorData["series"][0]
  inferenceSeries = inferenceData["series"][0]

  sensorValues = sensorSeries["values"]
  sensorColumns = sensorSeries["columns"]
  inferenceValues = inferenceSeries["values"]
  inferenceColumns = inferenceSeries["columns"]

  columnsOut = sensorColumns + inferenceColumns[1:]
  valuesOut = []
  sensorStep = 0
  inferenceStep = 0

  # This loop matches HTM inferences with sensor data of the same timestamp.
  # Progresses through all sensor data and zips inferences into a new output
  # list.
  for sensorValue in sensorValues:
    sensorTime = iso8601.parse_date(sensorValue[sensorColumns.index("time")])
    inferenceTime = iso8601.parse_date(inferenceValues[inferenceStep][sensorColumns.index("time")])
    while inferenceTime < sensorTime:
      inferenceStep += 1
      inferenceTime = iso8601.parse_date(inferenceValues[inferenceStep][sensorColumns.index("time")])
    if sensorTime == inferenceTime:
      valueOut = sensorValue + inferenceValues[inferenceStep][1:]
    else:
      valueOut = sensorValue + [None, None]
    valuesOut.append(valueOut)
    sensorStep += 1

  dataOut = {
    "series": [{
      "values": valuesOut,
      "name": sensorSeries["name"],
      "columns": columnsOut,
      "tags": sensorSeries["tags"]
    }]
  }

  return dataOut


def influxCopyPossible(fromMeta, toMeta):
  # Name and tags must be the same.
  if fromMeta["name"] != toMeta["name"] \
      or fromMeta["tags"] != toMeta["tags"]:
    return False
  # Ensure all columns exist in the destination schema.
  return all(x in toMeta["columns"] for x in fromMeta["columns"])


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
    databases = self._client.get_list_database()
    if database not in [d["name"] for d in databases]:
      if self._verbose:
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


  def saveResult(self, htmResult, point):
    timezone = "unknown"
    if "timezone" in point:
      timezone = point["timezone"]
    self.saveSensorData(point)
    if htmResult:
      self.saveHtmInference(
        htmResult, point["component"], point["stream"], point["time"], timezone
      )


  def listSensors(self):
    allSensors = self._client.get_list_series()
    sensorsOnly = (s for s in allSensors if not s["name"].endswith("_inference"))
    return sensorsOnly


  def queryMeasurement(self,
                       measurement,
                       component,
                       limit=None,
                       since=None,
                       aggregate=None,
                       database=None):
    toSelect = "value"

    if aggregate is not None:
      toSelect = "MEAN(value)"

    query = "SELECT {0} FROM {1} WHERE component = '{2}'"\
      .format(toSelect, measurement, component)

    if since is not None:
      query += " AND time > {0}s".format(since)

    if aggregate is None:
      query += " GROUP BY *"
    else:
      query += " GROUP BY time({0}) fill(previous)".format(aggregate)

    query += " ORDER BY time DESC"

    if limit is not None:
      query += " LIMIT {0}".format(limit)

    print query

    response = self._client.query(query, database=database)

    # Don't process empty responses
    if len(response) < 1:
      return []

    data = response.raw
    # Because of the descending order in the query, we want to reverse the data so
    # it is actually in ascending order. The descending order was really just to get
    # the latest data.
    data["series"][0]["values"] = list(reversed(data["series"][0]["values"]))
    return data


  def getSensorData(self, measurement, component, limit=None, since=None, aggregate=None):
    sensorData = self.queryMeasurement(measurement, component, limit=limit, since=since, aggregate=aggregate)
    inferenceData = self.queryMeasurement(measurement + "_inference", component, limit=limit, since=since)
    return zipSensorAndInferenceData(sensorData, inferenceData)


  def transfer(self, **kwargs):
    fromDb = kwargs["from"]
    toDb = kwargs["to"]
    component = kwargs["component"]
    measurement = kwargs["measurement"]
    limit = kwargs["limit"]
    rawData = self.queryMeasurement(
      measurement, component, limit=1, database=toDb
    )
    if isinstance(rawData, list):
      raise Exception("Cannot transfer data because destination DB schema does not match source DB schema!")
    toSignature = rawData["series"][0]
    fromData = self.queryMeasurement(
      measurement, component, limit=limit, database=fromDb
    )["series"][0]

    if not influxCopyPossible(fromData, toSignature):
      if kwargs["verbose"]:
        from pprint import pprint
        pprint(fromData)
        pprint(toSignature)
      raise Exception("Cannot transfer data because destination DB schema does not match source DB schema!")

    payload = []

    for point in fromData["values"]:
      payload.append({
        "tags": fromData["tags"],
        "time": point[0],
        "measurement": measurement,
        "fields": {
          "value": float(point[1])
        }
      })

    self._client.write_points(payload)



