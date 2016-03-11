#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015-2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# ----------------------------------------------------------------------
import sys
import os
import json
import time
from datetime import datetime
from optparse import OptionParser

import requests
import iso8601
from hitcpy import HITC
from influxhtm import InfluxHtmClient

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

get_class = lambda x: globals()[x]

def createOptionsParser():
  parser = OptionParser(
    usage="%prog <subject>:<action> [options]"
  )

  parser.add_option(
    "-v",
    "--verbose",
    action="store_true",
    default=False,
    dest="verbose",
    help="Print debugging statements.")
  parser.add_option(
    "-g",
    "--guid",
    dest="guid",
    help="Model id.")
  parser.add_option(
    "-p",
    "--param-path",
    dest="paramPath",
    help="Path to model params JSON file.")
  parser.add_option(
    "-c",
    "--component",
    dest="component",
    help="Sensor component.")
  parser.add_option(
    "-m",
    "--measurement",
    dest="measurement",
    help="Sensor measurement.")
  parser.add_option(
    "-l",
    "--limit",
    dest="limit",
    default=None,
    help="Sensor data limit when fetching.")
  parser.add_option(
    "-s",
    "--since",
    dest="since",
    default=None,
    help="Sensor data lower time bound.")
  parser.add_option(
    "-f",
    "--from",
    dest="from",
    default=None,
    help="InfluxDB database name.")
  parser.add_option(
    "-t",
    "--to",
    dest="to",
    default=None,
    help="InfluxDB database name.")
  parser.add_option(
    "-a",
    "--aggregation",
    dest="aggregation",
    default=None,
    help="Time period for aggregation (1s, 1m, 1d, 1w, etc.)")

  return parser



class models:


  def __init__(self, hitcClient, ihtmClient, verbose=False):
    self._hitcClient = hitcClient
    self._ihtmClient = ihtmClient
    self._verbose = verbose


  def list(self, **kwargs):
    print "HITC Models:"
    models = self._hitcClient.get_all_models()
    if len(models) < 1:
      print "None"
    else:
      for m in models:
        print " - {}models/{}".format(m.url, m.guid)

    print "\nInfluxDB Stored Models:"
    models = self._ihtmClient.getHtmModels()
    if len(models) < 1:
      print "None"
    else:
      for m in models:
        print m


  def create(self, **kwargs):
    validateKwargs(["measurement", "component", "paramPath"], kwargs)
    measurement = kwargs["measurement"]
    component = kwargs["component"]
    paramPath = kwargs["paramPath"]
    sensor = self._ihtmClient.getSensor(
      measurement=measurement, component=component
    )
    if sensor is None:
      raise ValueError(
        "No sensor exists for measurement={} & component={}"
          .format(measurement, component)
      )
    with(open(paramPath, "r")) as paramFile:
      params = json.loads(paramFile.read())
    params["guid"] = "{}_{}_model".format(component, measurement)
    try:
      model = self._hitcClient.create_model(params)
      print model
      print "Created HITC model '%s'" % model.guid
    except KeyError:
      print "Model with id '%s' already exists." % params["guid"]


  def delete(self, **kwargs):
    validateKwargs(["guid"], kwargs)
    guid = kwargs["guid"]
    for model in self._hitcClient.get_all_models():
      if model.guid == guid:
        model.delete()
        print "Deleted model '%s'" % guid
    if kwargs["measurement"] is not None and kwargs["component"] is not None:
      # Safeguard to ensure original sensor data is not accidentally deleted.
      measurement = kwargs["measurement"]
      if not measurement.endswith("_inference"):
        measurement = "{}_inference".format(measurement)
      sensors(
        self._hitcClient, self._ihtmClient, self._verbose
      ).delete(measurement=measurement, component=kwargs["component"])


  def deleteAll(self, **kwargs):
    for model in self._hitcClient.get_all_models():
      kwargs["guid"] = model.guid
      self.delete(**kwargs)


  def load(self, **kwargs):
    validateKwargs(["measurement", "component"], kwargs)
    measurement = kwargs.pop("measurement")
    component = kwargs.pop("component")
    guid = "{}_{}_model".format(component, measurement)

    # Get the HITC model
    hitcModel = self._hitcClient.get_model(guid)
    if hitcModel is None:
      raise ValueError("You must create a model first.")

    # Get the influxhtm Sensor interface
    sensor = self._ihtmClient.getSensor(
      measurement=measurement, component=component
    )

    # Get the data!
    data = sensor.getData(**kwargs)["series"][0]
    dataValues = data["values"]
    if self._verbose:
      print "Pulled {} data points from InfluxDB...".format(len(dataValues))

    # Get or create an HtmSensorModel so we can write HTM results.
    htmSensorModel = sensor.getHtmModel()
    if htmSensorModel is None:
      htmSensorModel = sensor.createHtmModel(
        "{}models/{}".format(hitcModel.url, hitcModel.guid)
      )

    count = 0
    for point in dataValues:
      pointTime = point[0]
      results = self._runOneDataPoint(
        self._hitcClient, guid, iso8601.parse_date(pointTime), point[1]
      )
      # Write the model results.
      htmSensorModel.writeResult(pointTime, results)

      count += 1
      if self._verbose and count % 50 == 0:
        print "Loaded {} data points into model '{}' so far..." \
          .format(count, guid)
    if self._verbose:
      print "Loaded {} data points into model '{}'.".format(count, guid)


  def _runOneDataPoint(self, hitcClient, modelId, inputTime, value):
    # Get date from string if it is a string.
    if isinstance(inputTime, basestring):
      timeObj = datetime.strptime(inputTime, DATE_FORMAT)
    # Otherwise we assume it is a date object.
    else:
      timeObj = inputTime

    timestamp = int(time.mktime(timeObj.timetuple()))

    dataRow = {
      "c0": timestamp,
      "c1": value
    }

    if self._verbose:
      print dataRow

    # There is only one value in the result list, so pop() it off.
    return hitcClient.get_model(modelId).run(dataRow).pop()



class sensors:


  def __init__(self, hitcClient, ihtmClient, verbose=False):
    self._hitcClient = hitcClient
    self._ihtmClient = ihtmClient
    self._verbose = verbose


  def data(self, **kwargs):
    validateKwargs(["measurement", "component"], kwargs)
    sensor = self._ihtmClient.getSensor(
      measurement=kwargs.pop("measurement"),
      component=kwargs.pop("component")
    )
    rawData = sensor.getData(**kwargs)

    if len(rawData) == 0:
      print "No data."
    else:
      data = rawData["series"][0]
      values = data["values"]
      columns = data["columns"]
      print columns
      for v in values:
        print(v)


  def inference(self, **kwargs):
    validateKwargs(["measurement", "component"], kwargs)
    rawData = self._sensorClient.queryMeasurement(
      kwargs["measurement"] + "_inference", kwargs["component"],
      limit=kwargs["limit"])
    if len(rawData) == 0:
      print "No data."
    else:
      data = rawData["series"][0]
      values = data["values"]
      columns = data["columns"]
      print columns
      for v in values:
        print(v)



  def list(self, **kwargs):
    for s in self._ihtmClient.getSensors():
      print s


# Util functions

def extractIntent(command):
  return command.split(":")


def validateKwargs(requiredKeys, kwargs):
  for key in requiredKeys:
    if kwargs[key] is None:
      requiredOptions = " and "\
        .join(["--{}".format(key) for key in requiredKeys])
      print "You must provide {} for this call.".format(requiredOptions)
      exit(-1)


def getHitcUrl():
  if "HITC" not in os.environ:
    return None
  url = os.environ["HITC"]
  if url.endswith("/"):
    url = url[:-1]
  return url


def getHitcClient():
  hitcClient = None
  hitcUrl = getHitcUrl()
  if hitcUrl is not None and len(hitcUrl) > 0:
    try:
      hitcClient = HITC(hitcUrl)
    except requests.exceptions.ConnectionError:
      print "WARNING: No HITC is available at {}".format(hitcUrl)
      print "         No HTM functions will be available."

  return hitcClient


def runAction(subject, action, **kwargs):
  hitcClient = getHitcClient()
  database = os.environ["INFLUX_DB"]
  verbose = kwargs["verbose"]
  ihtmClient = InfluxHtmClient(
    database, verbose=verbose
  )
  try:
    subjectType = get_class(subject)(hitcClient, ihtmClient, verbose=verbose)
  except KeyError as error:
    print "Incorrect subject '{}'".format(subject)
    raise error
  actionFunction = getattr(subjectType, action)
  # print "\n* * *\n"
  actionFunction(**kwargs)


def main():
  parser = createOptionsParser()
  options, args = parser.parse_args(sys.argv[1:])
  if len(args) < 1:
    raise ValueError("Please provide a command.")
  subject, action = extractIntent(args[0])
  runAction(subject, action, **vars(options))


if __name__ == "__main__":
  main()
