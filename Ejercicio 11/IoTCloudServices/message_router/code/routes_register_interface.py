import requests
import os

def register_completed_route(params):
    host = os.getenv('ROUTES_MICROSERVICE_ADDRESS')
    port = os.getenv('ROUTES_MICROSERVICE_PORT')
    r = requests.post(f'http://{host}:{port}/routes/complete/', json=params)
    
    if r.status_code == 500:
        return False
    if r.status_code == 201:
        return True
       
    return False

def register_delivered_route():
    host = os.getenv('ROUTES_MICROSERVICE_ADDRESS')
    port = os.getenv('ROUTES_MICROSERVICE_PORT')
    r = requests.post(f'http://{host}:{port}/routes/deliver/')

    if r.status_code == 500:
        return False
    if r.status_code == 201:
        return True

    return False
