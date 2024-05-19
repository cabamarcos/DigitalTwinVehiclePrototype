from flask import Flask, request
from flask_cors import CORS
from vehicles_db_manager import *
import os

app = Flask(__name__)
CORS(app)

@app.route('/vehicles/register/', methods=['POST'])
def save_vehicle_info():
    params = request.get_json()
    plate = register_new_vehicle(params)
    if plate != "":
        return {"Plate": plate}, 201
    else:
        return {"result": "error inserting a new vehicle"}, 500
    
@app.route('/vehicles/retrieve/', methods=['GET'])
def retrieve_vehicles():
    return get_active_vehicles()

@app.route('/vehicles/disconnect/', methods=['POST'])
def disconnect_vehicle():
    params = request.get_json()
    result = deactivate_vehicle(params)
    if result:
        return {"result": "vehicle disconnected"}, 201
    else:
        return {"result": "error disconnecting the vehicle"}, 500


if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(debug=True, host= HOST, port=PORT)
