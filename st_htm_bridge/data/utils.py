import os
import time
from datetime import datetime

from hitcpy import HITC


def getHitcUrl():
  if "HITC" not in os.environ:
    return None
  url = os.environ["HITC"]
  if url.endswith("/"):
    url = url[:-1]
  return url


def runOneDataPoint(hitcClient, modelId, inputTime, value):
  if isinstance(inputTime, basestring):
    timestamp = int(time.mktime(datetime.strptime(inputTime, DATE_FORMAT).timetuple()))
  else:
    timestamp = int(time.mktime(inputTime.timetuple()))
  dataRow = {
    "c0": timestamp,
    "c1": value
  }
  # There is only one value in the result list, so pop() it off.
  return hitcClient.get_model(modelId).run(dataRow).pop()


def getHitcClient():
  hitcClient = None
  hitcUrl = getHitcUrl()
  if hitcUrl is not None and len(hitcUrl) > 0:
    hitcClient = HITC(hitcUrl)
  return hitcClient
