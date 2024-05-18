import paho.mqtt.client as mqtt
import os
from flask import Flask, request
from flask_cors import CORS
import json
import threading
from telemetry_register_interface import register_telemetry
from vehicle_register_interface import register_vehicle, disconnect_vehicle
from routes_register_interface import register_completed_route, register_delivered_route

route_mid = ""

app = Flask(__name__)
CORS(app)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    
    if rc == 0:
        STATE_TOPIC = "/fic/vehicles/+/telemetry"
        INIT_TOPIC = "/fic/vehicles/+/request_plate"
        EVENTS_TOPIC = "/fic/vehicles/+/event"
        client.subscribe(INIT_TOPIC)
        print("Subscribed to", INIT_TOPIC)
        client.subscribe(STATE_TOPIC)
        print("Subscribed to", STATE_TOPIC)
        client.subscribe(EVENTS_TOPIC)
        print("Subscribed to", EVENTS_TOPIC)
        print()

def on_message(client, userdata, msg):
    print("Received message:", msg.topic)
    print()
    
    topic = msg.topic.split("/")
    # Request plate
    if topic[-1] == "request_plate":
        input_data = json.loads(msg.payload.decode())
        request_data = {"vehicle_id": input_data["vehicle_id"]}
        vehicle_plate = register_vehicle(request_data)
        # Si no se ha podido registrar el vehículo
        if vehicle_plate is None:
            print("Error al registrar el vehículo")
            client.publish("/fic/vehicles/" + input_data["vehicle_id"] + 
                           "/config", payload='{"Plate":"Not Available"}', qos=1, retain=False)
        # Vehículo registrado correctamente
        else:
            plate_json = {"Plate": vehicle_plate}
            client.publish("/fic/vehicles/" + input_data["vehicle_id"] + "/config", 
                        payload=json.dumps(plate_json), qos=1, retain=False)
            print("Publicado", vehicle_plate, "en TOPIC", msg.topic)
    # Telemetry
    if topic[-1] == "telemetry":
        str_received_telemetry = msg.payload.decode()
        received_telemetry = json.loads(str_received_telemetry)
        result = register_telemetry(received_telemetry)
        if result == False:
            print("Error al registrar la telemetría")
        else:
            print("Telemetría registrada correctamente")
    # Event
    if topic[-1] == "event":
        event = json.loads(msg.payload.decode())
        # Ruta completada
        if event["Event"] == "Route Completed":
            input_data = json.loads(msg.payload.decode())
            request_data = {"Plate": input_data["Plate"]}
            result = register_completed_route(request_data)
            if result == False:
                print("Error al registrar la ruta completada")
            else:
                print("Ruta completada de " + input_data["Plate"] + " registrada correctamente")
                print()
        # Vehículo desconectado
        if event["Event"] == "Vehicle Disconnected":
            input_data = json.loads(msg.payload.decode())
            request_data = {"vehicle_id": input_data["vehicle_id"]}
            result = disconnect_vehicle(request_data)
            if result == False:
                print("Error al desconectar el vehículo")
            else:
                print("Vehículo " + input_data["vehicle_id"] + " desconectado correctamente")
                print()

def on_publish(client, userdata, mid):
    if mid == route_mid:
        print("Ruta recibida por el vehículo")
        result = register_delivered_route()
        if result == False:
            print("Error al registrar la ruta entregada")
        else:
            print("Ruta entregada registrada correctamente")
            print()

@app.route('/routes/send/', methods=['POST'])
def send_route():
    global route_mid
    try:
        params = request.get_json()
        route = {"Origin": params["origin"], "Destination": params["destination"]}
        mid = client.publish("/fic/vehicles/" + params["plate"] + "/routes",
                       payload=json.dumps(route), qos=1, retain=False)
        route_mid = mid[1]
        print("\nRuta enviada a " + params["plate"])
        print()
        return {"Result": "Route successfully sent"}, 201
    except:
        return {"Result": "Internal Server Error"}, 500

def mqtt_listener():
    client.username_pw_set(username="fic_server", password="fic_password")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_forever()


if __name__ == "__main__":
    global client

    # Hilo para comunicación MQTT
    client = mqtt.Client()
    t1 = threading.Thread(target=mqtt_listener, daemon=True)
    t1.start()

    # API REST
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(debug=True, host=HOST, port=PORT)
