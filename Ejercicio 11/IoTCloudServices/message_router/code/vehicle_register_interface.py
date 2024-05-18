import requests
import os

def register_vehicle(data):
    host = os.getenv('VEHICLES_MICROSERVICE_ADDRESS')
    port = os.getenv('VEHICLES_MICROSERVICE_PORT')
    r = requests.post('http://' + host + ':' + port + '/vehicles/register/', json=data)

    if r.status_code == 500:
        return None
    if r.status_code == 201:
        return r.json()["Plate"]
       
    return None

def disconnect_vehicle(data):
    host = os.getenv('VEHICLES_MICROSERVICE_ADDRESS')
    port = os.getenv('VEHICLES_MICROSERVICE_PORT')
    r = requests.post('http://' + host + ':' + port + '/vehicles/disconnect/', json=data)

    if r.status_code == 500:
        return False
    if r.status_code == 201:
        return True

    return False
    