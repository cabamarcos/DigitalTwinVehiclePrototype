from flask import Flask, request
from flask_cors import CORS
from routes_db_manager import *
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/routes/assign/', methods=['POST'])
def assign_route():
    params = request.get_json()
    result = assign_new_route(params)
    if result:
        host = os.getenv('MESSAGE_ROUTER_ADDRESS')
        port = os.getenv('MESSAGE_ROUTER_PORT')
        r = requests.post(f'http://{host}:{port}/routes/send/', json=params)

        if r.status_code == 201:
            return {"result": "Route assigned"}, 201

    return {"result": "Error assigning a new route"}, 500
    
@app.route('/routes/retrieve/', methods=['GET'])
def retrieve_routes():
    params = request.get_json()
    return get_routes_assigned_to_vehicle(params)

@app.route('/routes/deliver/', methods=['POST'])
def deliver_route():
    result = register_delivered_route()
    if result:
        return {"result": "Delivered route updated"}, 201
    else:
        return {"result": "Error updating delivered route"}, 500

@app.route('/routes/complete/', methods=['POST'])
def complete_route():
    params = request.get_json()
    result = register_completed_route(params)
    if result:
        return {"result": "Completed route updated"}, 201
    else:
        return {"result": "Error updating completed route"}, 500


if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(debug=True, host=HOST, port=PORT)
