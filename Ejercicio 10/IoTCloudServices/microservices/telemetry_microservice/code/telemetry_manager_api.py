from flask import Flask, request
from flask_cors import CORS
from telemetry_db_manager import *
import os

app = Flask(__name__)
CORS(app)

@app.route('/telemetry/register/', methods=['POST'])
def save_vehicle_info():
    params = request.get_json()
    if register_new_telemetry(params):
        return {"result": "Telemetry registered"}, 201
    else:
        return {"result": "Error registering telemetries"}, 500
    
@app.route('/telemetry/vehicle/positions/', methods=['GET'])
def retrieve_vehicles_last_position():
    result = get_vehicles_last_position()
    if result["Error Message"] is None:
        return result, 201
    else:
        return result, 500

@app.route('/telemetry/vehicle/detailed_info/', methods=['GET'])
def retrieve_vehicle_detailed_info():
    params = request.get_json()
    result = get_vehicle_detailed_info(params)
    if result["Error Message"] is None:
        return result, 201
    else:
        return result, 500

if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(debug=True, host= HOST, port=PORT)
