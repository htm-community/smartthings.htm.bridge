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
                       ):
    print "Saving HTM inference..."
    anomalyScore = result["inferences"]["anomalyScore"]
    anomalyLikelihood = result["anomalyLikelihood"]

    payload = [{
      "tags": {
        "component": component,
      },
      "time": timestamp,
      "measurement": measurement + '_inference',
      "fields": {
        "anomalyScore": anomalyScore,
        "anomalyLikelihood": anomalyLikelihood
      }
    }]

    self._client.write_points(payload)


  def saveHtmResults(self, measurement, component, results):
    if self._verbose:
      print "Saving HTM results..."
    payload = []
    for result in results:
      anomalyScore = result["results"]["inferences"]["anomalyScore"]
      anomalyLikelihood = result["results"]["anomalyLikelihood"]

      payload.append({
        "tags": {
          "component": component,
        },
        "time": result["time"],
        "measurement": measurement + '_inference',
        "fields": {
          "anomalyScore": anomalyScore,
          "anomalyLikelihood": anomalyLikelihood
        }
      })
    if self._verbose:
      print "Writing {} points...".format(len(payload))
    self._client.write_points(payload)


  def saveSensorData(self, point):
    print "Saving sensor data point..."

    payload = [{
      "tags": {
        "component": point["component"],
      },
      "time": point["time"],
      "measurement": point["stream"],
      "fields": {
        "value": float(point["value"]),
      }
    }]

    self._client.write_points(payload)


  def zipSensorAndInferenceData(self, sensorData, inferenceData):

    # If inferenceData is empty, just return sensorData
    if isinstance(inferenceData, list):
      # Just return the sensor data and warn.
      if self._verbose:
        print("WARNING: No HTM inference data available. "
              "Only returning sensor data.")
      return sensorData

    sensorSeries = sensorData["series"][0]
    inferenceSeries = inferenceData["series"][0]

    sensorValues = sensorSeries["values"]
    sensorColumns = sensorSeries["columns"]
    sensorTimeIndex = sensorColumns.index("time")
    inferenceValues = inferenceSeries["values"]
    inferenceColumns = inferenceSeries["columns"]
    inferenceTimeIndex = inferenceColumns.index("time")

    columnsOut = sensorColumns + inferenceColumns[1:]
    valuesOut = []
    prevSensor = None
    prevAnomScore = None
    prevAnomLikely = None

    while len(sensorValues) > 0 and len(inferenceValues) > 0:
      sensorTime = sensorValues[0][sensorTimeIndex]
      inferenceTime = inferenceValues[0][inferenceTimeIndex]
      if sensorTime == inferenceTime:
        sensorValue = sensorValues.pop(0)
        inferenceValue = inferenceValues.pop(0)
        valuesOut.append(sensorValue + inferenceValue[1:])
        prevSensor = sensorValue[1]
        prevAnomScore = inferenceValue[1]
        prevAnomLikely = inferenceValue[2]
      elif sensorTime < inferenceTime:
        sensorValue = sensorValues.pop(0)
        valuesOut.append(sensorValue + [prevAnomScore, prevAnomLikely])
        prevSensor = sensorValue[1]
      else:
        inferenceValue = inferenceValues.pop(0)
        valuesOut.append([inferenceValue[0], prevSensor] + inferenceValue[1:])
        prevAnomScore = inferenceValue[1]
        prevAnomLikely = inferenceValue[2]

    dataOut = {
      "series": [{
        "values": valuesOut,
        "name": sensorSeries["name"],
        "columns": columnsOut,
      }]
    }

    return dataOut


  def listSensors(self):
    sensors = self._client.get_list_series()
    if not self._verbose:
      # Strip out inference readings unless verbose.
      sensors = (
        s for s in sensors if not s["name"].endswith("_inference")
      )
    return sensors


  def getEarliestTimestamp(self, measurement, component):
    query = ("SELECT * FROM {0} WHERE component = '{1}' "
             "ORDER BY time LIMIT 1").format(measurement, component)
    if self._verbose:
      print query
    response = self._client.query(query)
    return response.raw["series"][0]["values"][0][0]


  def queryMeasurement(self,
                       measurement,
                       component,
                       selection="value",
                       limit=None,
                       since=None,
                       aggregation=None,
                       database=None):
    toSelect = selection

    if aggregation is not None:
      toSelect = "MEAN(value)"

    query = "SELECT {0} FROM {1} WHERE component = '{2}'"\
      .format(toSelect, measurement, component)

    if since is not None:
      # since might be an integer timestamp or a time string. If it is a time
      # string, we'll just put single quotes around it to play nice with Influx.
      if isinstance(since, basestring):
        since = "'{}'".format(since)
      query += " AND time > {0}".format(since)

    if aggregation is None:
      query += " GROUP BY *"
    else:
      query += " GROUP BY time({0}) fill(previous)".format(aggregation)

    query += " ORDER BY time DESC"

    if limit is not None:
      query += " LIMIT {0}".format(limit)

    if self._verbose:
      print query

    response = self._client.query(query, database=database)

    # Don't process empty responses
    if len(response) < 1:
      return []

    data = response.raw
    # Because of the descending order in the query, we want to reverse the data
    # so it is actually in ascending order. The descending order was really just
    # to get the latest data.
    data["series"][0]["values"] = list(reversed(data["series"][0]["values"]))
    return data


  def getInferenceData(self, measurement, component, **kwargs):
    return self.queryMeasurement(
      measurement + "_inference", component,
      selection="anomalyLikelihood, anomalyScore",
      **kwargs
    )


  def getSensorData(self,
                    measurement,
                    component,
                    limit=None,
                    since=None,
                    aggregation=None):
    if since is None:
      since = self.getEarliestTimestamp(measurement, component)
    return self.queryMeasurement(
      measurement, component, limit=limit, since=since, aggregation=aggregation
    )



  def getCombinedSensorData(self,
                    measurement,
                    component,
                    limit=None,
                    since=None,
                    aggregation=None):
    if since is None:
      since = self.getEarliestTimestamp(measurement, component)
    sensorData = self.getSensorData(
      measurement, component, limit=limit, since=since, aggregation=aggregation
    )
    inferenceData = self.getInferenceData(
      measurement, component,
      limit=limit, since=since
    )
    return self.zipSensorAndInferenceData(sensorData, inferenceData)


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
      raise Exception("Cannot transfer data because destination DB schema does "
                      "not match source DB schema!")
    toSignature = rawData["series"][0]
    fromData = self.queryMeasurement(
      measurement, component, limit=limit, database=fromDb
    )["series"][0]

    if not influxCopyPossible(fromData, toSignature):
      if kwargs["verbose"]:
        from pprint import pprint
        pprint(fromData)
        pprint(toSignature)
      raise Exception("Cannot transfer data because destination DB schema does "
                      "not match source DB schema!")

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


  def delete(self, measurement, component):
    self._client.delete_series(measurement=measurement, tags={"component": component})
