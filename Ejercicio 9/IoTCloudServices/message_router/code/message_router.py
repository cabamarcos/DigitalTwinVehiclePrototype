import paho.mqtt.client as mqtt
import os
import time
import random
import json

index_vehicle = 0
connected_vehicles = []
available_plates = ["0001BBB", "0002BBB", "0003BBB", "0004BBB",
                    "0005BBB", "0006BBB", "0007BBB", "0008BBB", "0009BBB",
                    "0010BBB"]
pois = ["Ayuntamiento de Leganes",
"Ayuntamiento de Alcorcón", "Ayuntamiento de Móstoles",
"Universidad Carlos III de Madrid - Campus de Leganés",
"Universidad Carlos III de Madrid - Campus de Getafe",
"Universidad Carlos III de Madrid - Campus de Puerta de Toledo", 
"Universidad Carlos III de Madrid - Campus de Colmenarejo",
"Ayuntamiento de Navalcarnero", "Ayuntamiento de Arroyomolinos", 
"Ayuntamiento de Carranque", "Ayuntamiento de Alcalá de Henares", 
"Ayuntamiento de Guadarrama", "Ayuntamiento de la Cabrera", 
"Ayuntamiento de Aranjuez"]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    
    if rc == 0:
        STATE_TOPIC = "/fic/vehicles/+/telemetry"
        INIT_TOPIC = "/fic/vehicles/+/request_plate"
        EVENTS_TOPIC = "/fic/vehicles/+/event"
        client.subscribe(INIT_TOPIC)
        print("Subscribed to ", INIT_TOPIC)
        client.subscribe(STATE_TOPIC)
        print("Subscribed to ", STATE_TOPIC)
        client.subscribe(EVENTS_TOPIC)
        print("Subscribed to ", EVENTS_TOPIC)
        print()

def get_vehicle_plate(vehicle_id):
    for vehicle in connected_vehicles:
        if vehicle["id"] == vehicle_id:
            return vehicle["Plate"]
    return None

def on_message(client, userdata, msg):
    global index_vehicle
    print("Received message:", msg.topic, msg.payload)
    print()
    
    topic = msg.topic.split("/")
    # Request plate
    if topic[-1] == "request_plate":
        requested_id = get_vehicle_plate(msg.payload.decode())
        if requested_id is not None:
                plate_json = '{"Plate":"' + requested_id + '"}'
                client.publish("/fic/vehicles/" + msg.payload.decode() + 
                               "/config", payload=plate_json, qos=1, retain=False)
        # Si hay menos de 10 vehículos conectados, se asigna una matrícula
        elif index_vehicle < 10:
            vehicle_plate = available_plates[index_vehicle]
            new_vehicle = {"id": msg.payload.decode(),
                           "Plate": vehicle_plate,
                           "Route": {"Origin": None, "Destination": None}}
            connected_vehicles.append(new_vehicle)
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
        telemetry = json.loads(msg.payload.decode())
        # Si el fichero no existe, se crea
        if not os.path.exists(file_name):
            with open(file_name, "w") as file:
                file.write("[]")
        # Leer el fichero
        with open(file_name, "r") as file:
            telemetry_list = json.load(file)
        # Añaadir la nueva telemetría
        telemetry_list.append(telemetry)
        # Guardar las telemetrías
        with open(file_name, "w") as file:
            json.dump(telemetry_list, file)
        print("Telemetry saved in", file_name)
        print()
    # Event
    if topic[-1] == "event":
        event = json.loads(msg.payload.decode())
        # Ruta completada
        if event["Event"] == "Route Completed":
            for vehicle in connected_vehicles:
                if vehicle["id"] == topic[-2]:
                    # Retirar la ruta del vehículo
                    vehicle["Route"]["Origin"] = None
                    vehicle["Route"]["Destination"] = None
                    print("Ruta completada por el vehículo", vehicle["Plate"])
                    print()
                    break

def send_route(vehicle_index, client):
    global connected_vehicles
    # Si el vehículo no tiene una ruta asignada, se le asigna
    if connected_vehicles[vehicle_index]["Route"]["Origin"] is None:
        # Seleccionar origen y destino aleatorios sin repetir
        origin = random.choice(pois)
        destination = random.choice(pois)
        while origin == destination:
            destination = random.choice(pois)
        # Enviar la ruta al vehículo
        route = {"Origin": origin, "Destination": destination}
        client.publish("/fic/vehicles/" + 
                       connected_vehicles[vehicle_index]["id"] + "/routes",
                       payload=json.dumps(route), qos=1, retain=False)
        print("Ruta enviada al vehículo", connected_vehicles[vehicle_index]["Plate"])
        print()
        # Asignar la ruta al vehículo
        connected_vehicles[vehicle_index]["Route"]["Origin"] = origin
        connected_vehicles[vehicle_index]["Route"]["Destination"] = destination

def main():
    client = mqtt.Client()
    client.username_pw_set(username="fic_server", password="fic_password")

    client.on_connect = on_connect
    client.on_message = on_message

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_start()

    while True:
        if len(connected_vehicles) > 0:
            # Seleccionar un vehículo aleatorio
            target_vehicle = random.randint(0, len(connected_vehicles) - 1)
            # Enviar una ruta al vehículo seleccionado
            send_route(target_vehicle, client)
            time.sleep(60)
        time.sleep(2)
        
    client.loop_stop()


if __name__ == "__main__":
    main()
