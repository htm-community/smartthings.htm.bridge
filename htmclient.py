import json
import requests

URL = "http://localhost:5000/"

def post(url, params=None):
    return requests.post(URL+url, data=params)

def get(url, params=None):
    return requests.get(URL+url, params=params)

def put(url, params=None):
    return requests.put(URL+url, data=params)

def createModel(model_spec):
    response = post('models', model_spec)
    r = response.json()
    if response.status_code == 200:
        return r['guid']
    else:
        raise Exception("Could not create model: " + r['error'])

def getModel(model):
    return get('models/'+model)

def listModels():
    return get('models').json()


def sendData(modelId, point):
    resp = put('models/' + modelId, json.dumps(point))
    print resp
    respJson = resp.json()
    return respJson
