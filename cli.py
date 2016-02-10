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
import json
from optparse import OptionParser

import iso8601

from runapp import getHitcClient, runOneDataPoint
from influxclient import getSensorData


global verbose
get_class = lambda x: globals()[x]

def createOptionsParser():
  parser = OptionParser(
    usage="%prog [options]\n\n" +
    """
./cli.py models:list
./cli.py models:delete <guid>
./cli.py models:create <model-param-path>
    """
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
  
  return parser



class models:

  
  def __init__(self, client):
    self.client = client


  def list(self, **kwargs):
    models = self.client.get_all_models()
    if len(models) < 1:
      print "NO MODELS"
    else:
      print "CURRENT MODELS:"
      for m in models:
        print " - %s" % m.guid


  def create(self, **kwargs):
    with(open(kwargs["paramPath"], "r")) as paramFile:
      params = json.loads(paramFile.read())
      if "guid" in kwargs and kwargs["guid"] is not None:
        params["guid"] = kwargs["guid"]
      try:
        model = self.client.create_model(params)
        print "Created model '%s'" % model.guid
      except KeyError:
        print "Model with id '%s' already exists." % kwargs["guid"]


  def delete(self, **kwargs):
    guid = kwargs["guid"]
    for model in self.client.get_all_models():
      if model.guid == guid:
        model.delete()
        print "Deleted model '%s'" % guid

  def deleteAll(self, **kwargs):
    for model in self.client.get_all_models():
      model.delete()
      print "Deleted model '%s'" % model.guid
  
  
  def loadData(self, **kwargs):
    data = getSensorData(
      kwargs["measurement"], kwargs["component"], 
      limit=kwargs["limit"], sensorOnly=True
    )["series"][0]
    guid = kwargs["guid"]
    results = []
    for point in data["values"]:
      results.append(runOneDataPoint(
        self.client, guid, iso8601.parse_date(point[0]), point[1]
      ))
    print "Loaded %i data points into model '%s'." % (len(results), guid)
    
    


class data:

  
  def __init__(self, client):
    self.client = client


  def list(self, **kwargs):
    data = getSensorData(
      kwargs["measurement"], kwargs["component"], 
      limit=kwargs["limit"], sensorOnly=True
    )["series"][0]
    values = data["values"]
    columns = data["columns"]
    print columns
    for v in values:
      print(v)


def extractIntent(command):
  return command.split(":")


def runAction(subject, action, **kwargs):
  client = getHitcClient()
  subjectType = get_class(subject)(client)
  actionFunction = getattr(subjectType, action)
  print "\n* * *\n"
  actionFunction(**kwargs)
  
        

if __name__ == "__main__":
  global verbose
  parser = createOptionsParser()
  options, args = parser.parse_args(sys.argv[1:])
  verbose = options.verbose
  if len(args) < 1:
    raise ValueError("Please provide a command.")
  subject, action = extractIntent(args[0])
  runAction(subject, action, **vars(options))
