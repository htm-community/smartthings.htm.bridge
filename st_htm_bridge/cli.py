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
from optparse import OptionParser

import iso8601

from data import getHitcClient, runOneDataPoint, SensorClient


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
    help="Sensor data limit when fetching.")
  parser.add_option(
    "-f",
    "--from",
    dest="from",
    help="InfluxDB database name.")
  parser.add_option(
    "-t",
    "--to",
    dest="to",
    help="InfluxDB database name.")

  return parser



class models:


  def __init__(self, hitcClient, sensorClient):
    self._hitcClient = hitcClient
    self._sensorClient = sensorClient


  def list(self, **kwargs):
    models = self._hitcClient.get_all_models()
    if len(models) < 1:
      print "NO MODELS"
    else:
      print "CURRENT MODELS:"
      for m in models:
        print " - %s" % m.guid


  def create(self, **kwargs):
    if kwargs["paramPath"] is None:
      raise ValueError("User must provide --param-path to model params JSON file.")
    paramPath = kwargs["paramPath"]
    with(open(paramPath, "r")) as paramFile:
      params = json.loads(paramFile.read())
      if "guid" in kwargs and kwargs["guid"] is not None:
        params["guid"] = kwargs["guid"]
      try:
        model = self._hitcClient.create_model(params)
        print "Created model '%s'" % model.guid
      except KeyError:
        print "Model with id '%s' already exists." % kwargs["guid"]


  def delete(self, **kwargs):
    guid = kwargs["guid"]
    for model in self._hitcClient.get_all_models():
      if model.guid == guid:
        model.delete()
        print "Deleted model '%s'" % guid

  def deleteAll(self, **kwargs):
    for model in self._hitcClient.get_all_models():
      model.delete()
      print "Deleted model '%s'" % model.guid


  def loadData(self, **kwargs):
    data = self._sensorClient.getSensorData(
      kwargs["measurement"], kwargs["component"],
      limit=kwargs["limit"], sensorOnly=True
    )["series"][0]
    guid = kwargs["guid"]
    results = []
    for point in data["values"]:
      results.append(runOneDataPoint(
        self._hitcClient, guid, iso8601.parse_date(point[0]), point[1]
      ))
    print "Loaded %i data points into model '%s'." % (len(results), guid)




class sensors:


  def __init__(self, hitcClient, sensorClient):
    self._hitcClient = hitcClient
    self._sensorClient = sensorClient


  def data(self, **kwargs):
    validateKwargs(["measurement", "component"], kwargs)
    rawData = self._sensorClient.queryMeasurement(
      kwargs["measurement"], kwargs["component"], limit=kwargs["limit"]
    )
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
    for s in self._sensorClient.listSensors():
      name = s["name"]
      if not name.endswith("_inference"):
        print "component: %s\tmeasurement: %s" % (s["tags"][0]["component"], name)


  def transfer(self, **kwargs):
    validateKwargs([
      "from", "to", "component", "measurement"
    ], kwargs)
    self._sensorClient.transfer(**kwargs)


def extractIntent(command):
  return command.split(":")


def validateKwargs(requiredKeys, kwargs):
  for key in requiredKeys:
    if kwargs[key] is None:
      requiredOptions = " and "\
        .join(["--{}".format(key) for key in requiredKeys])
      print "You must provide {} for this call.".format(requiredOptions)
      exit(-1)



def runAction(subject, action, **kwargs):
  hitcClient = getHitcClient()
  database = os.environ["INFLUX_DB"]
  sensorClient = SensorClient(
    database, verbose=kwargs["verbose"]
  )
  subjectType = get_class(subject)(hitcClient, sensorClient)
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
