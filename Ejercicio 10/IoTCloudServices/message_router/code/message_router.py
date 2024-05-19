import paho.mqtt.client as mqtt
import os
import time
import random
import json
from telemetry_register_interface import register_telemetry
from vehicle_register_interface import register_vehicle, disconnect_vehicle

connected_vehicles = []
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
        print("Subscribed to", INIT_TOPIC)
        client.subscribe(STATE_TOPIC)
        print("Subscribed to", STATE_TOPIC)
        client.subscribe(EVENTS_TOPIC)
        print("Subscribed to", EVENTS_TOPIC)
        print()

def get_vehicle_plate(vehicle_id):
    for vehicle in connected_vehicles:
        if vehicle["id"] == vehicle_id:
            return vehicle["Plate"]
    return None

def on_message(client, userdata, msg):
    print("Received message:", msg.topic, msg.payload)
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
            # Si no existe el vehículo en la lista de vehículos conectados se añade
            if get_vehicle_plate(input_data["vehicle_id"]) is None:
                new_vehicle = {"id": input_data["vehicle_id"],
                               "Plate": vehicle_plate,
                               "Route": {"Origin": None, "Destination": None}}
                connected_vehicles.append(new_vehicle)
            # Publicar la matrícula en el topic del vehículo
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
            for vehicle in connected_vehicles:
                if vehicle["id"] == topic[-2]:
                    # Retirar la ruta del vehículo
                    vehicle["Route"]["Origin"] = None
                    vehicle["Route"]["Destination"] = None
                    print("Ruta completada por el vehículo", vehicle["Plate"])
                    print()
                    break
        if event["Event"] == "Vehicle Disconnected":
            input_data = json.loads(msg.payload.decode())
            request_data = {"vehicle_id": input_data["vehicle_id"]}
            result = disconnect_vehicle(request_data)
            if result == False:
                print("Error al desconectar el vehículo")
            else:
                # Eliminar el vehículo de la lista de vehículos conectados
                for vehicle in connected_vehicles:
                    if vehicle["id"] == topic[-2]:
                        connected_vehicles.remove(vehicle)
                        print("Vehículo " + vehicle["id"] + " desconectado correctamente")
                        print()

def send_route(vehicle_index, client):
    global connected_vehicles
    
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
    print()
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
            # Si el vehículo ya tiene una ruta asignada
            if connected_vehicles[target_vehicle]["Route"]["Origin"] is not None:
                time.sleep(0.5)
                continue
            # Enviar una ruta al vehículo seleccionado
            send_route(target_vehicle, client)
            time.sleep(60)
        time.sleep(2)
        
    client.loop_stop()


if __name__ == "__main__":
    main()
