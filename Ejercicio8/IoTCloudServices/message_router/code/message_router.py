import paho.mqtt.client as mqtt
import os
import json

index_vehicle = 0
connected_vehicles = {}
available_plates = ["0001BBB", "0002BBB", "0003BBB", "0004BBB",
                    "0005BBB", "0006BBB", "0007BBB", "0008BBB", "0009BBB",
                    "0010BBB"]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    
    if rc == 0:
        STATE_TOPIC = "/fic/vehicles/+/telemetry"
        INIT_TOPIC = "/fic/vehicles/+/request_plate"
        client.subscribe(INIT_TOPIC)
        print("Subscribed to ", INIT_TOPIC)
        client.subscribe(STATE_TOPIC)
        print("Subscribed to ", STATE_TOPIC)
        print()

def on_message(client, userdata, msg):
    global index_vehicle
    print("Received message:", msg.topic, msg.payload)
    print()
    
    topic = msg.topic.split("/")
    # Request plate
    if topic[-1] == "request_plate":
        requested_id = connected_vehicles.get(msg.payload.decode())
        if requested_id is not None:
                plate_json = '{"Plate":"' + connected_vehicles[requested_id] + '"}'
                client.publish("/fic/vehicles/" + msg.payload.decode() + 
                               "/config", payload=plate_json, qos=1, retain=False)
        # Si hay menos de 10 vehículos conectados, se asigna una matrícula
        elif index_vehicle < 10:
            vehicle_plate = available_plates[index_vehicle]
            connected_vehicles[msg.payload.decode()] = vehicle_plate
            index_vehicle += 1
            plate_json = '{"Plate":"' + vehicle_plate + '"}'
            client.publish("/fic/vehicles/" + msg.payload.decode() + 
                           "/config", payload=plate_json, qos=1, retain=False)
        else:
            print("La flota de vehículos ya está totalmente asignada")
            client.publish("/fic/vehicles/" + msg.payload.decode() + 
                           "/config", payload='{"Plate":"Not Available"}', qos=1, retain=False)
    # Telemetry
    if topic[-1] == "telemetry":
        file_name = "telemetry_" + topic[-2] + ".json"
        with open(file_name, "w") as file:
            file.write(msg.payload.decode())

def main():
    client = mqtt.Client()
    client.username_pw_set(username="fic_server", password="fic_password")

    client.on_connect = on_connect
    client.on_message = on_message

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_forever()


if __name__ == "__main__":
    main()
