import threading
import time
import json
import random
import os
import requests
from math import cos, sin, radians, acos

# Google Maps API Key
google_maps_api_key = "AIzaSyCU1SbRwkGRuynzpqtJUCbCvBIH_O0o4QM"

# Variables globales
t1 = None
t2 = None
t3 = None
t4 = None
brake = False
current_speed = 0
current_ldr = 0
current_obstacle_distance = 0.0
current_steering = 90
current_position = {}
current_leds = []
vehicleControlCommands = []
currentRouteDetailedSteps = []
routes = []


"""============= FUNCIONES ENTORNO ============="""

def simulate_obstacle(current_obstacle_distance):
    if current_obstacle_distance > 0.0:
        current_obstacle_distance += random.uniform(-5.0, 5.0)
        if current_obstacle_distance < 0.0:
            current_obstacle_distance = 0.0
    else:
        current_obstacle_distance += random.uniform(0.0, 50.0)

    return current_obstacle_distance

def simulate_ldr(current_ldr):
    if current_ldr > 0.0:
        current_ldr += random.uniform(-300.0, 300.0)
        if current_ldr < 0.0:
            current_ldr = 0.0
    else:
        current_ldr += random.uniform(0.0, 3000.0)
        
    return current_ldr

def environment_simulator():
    global current_ldr
    global current_obstacle_distance

    while True:
        current_ldr = simulate_ldr(current_ldr)
        current_obstacle_distance = simulate_obstacle(current_obstacle_distance)
        time.sleep(2)

"""============= FUNCIONES LUCES ============="""

def simulate_front_lights():
    # Luces de posición
    if current_ldr > 2000:
        current_light_intensity = 100
    else:
        current_light_intensity = 0

    # Luces intermitentes
    if current_steering < 80:
        front_left = {"Color": "White", "Intensity": current_light_intensity, "Blinking": "False"}
        # Luz intermitente amarilla derecha
        front_right = {"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"}
    elif current_steering > 100:
        front_right = {"Color": "White", "Intensity": current_light_intensity, "Blinking": "False"}
        # Luz intermitente amarilla izquierda
        front_left = {"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"}
    else:
        front_right = {"Color": "White", "Intensity": current_light_intensity, "Blinking": "False"}
        front_left = {"Color": "White", "Intensity": current_light_intensity, "Blinking": "False"}

    return front_left, front_right        

def simulate_rear_lights():
    # Luces de posición
    if current_ldr > 2000:
        current_light_intensity = 50
    else:
        current_light_intensity = 0
    
    # Luz de frenado
    if brake:
        current_light_intensity += 50
    else:
        current_light_intensity += 0

    # Luces intermitentes
    if current_steering < 80:
        rear_left = {"Color": "Red", "Intensity": current_light_intensity, "Blinking": "False"}
        # Luz intermitente amarilla derecha
        rear_right = {"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"}
    elif current_steering > 100:
        rear_right = {"Color": "Red", "Intensity": current_light_intensity, "Blinking": "False"}
        # Luz intermitente amarilla izquierda
        rear_left = {"Color": "Yellow", "Intensity": 100.0, "Blinking": "True"}
    else:
        rear_right = {"Color": "Red", "Intensity": current_light_intensity, "Blinking": "False"}
        rear_left = {"Color": "Red", "Intensity": current_light_intensity, "Blinking": "False"}

    return rear_left, rear_right

def led_manager():
    global current_leds
    while True:
        front_left, front_right = simulate_front_lights()
        rear_left, rear_right = simulate_rear_lights()
        current_leds = [front_left, front_right, rear_left, rear_right]
        time.sleep(2)

"""============= FUNCIONES RUTAS ============="""

def distance(p1, p2):
    p1Latitude = p1["latitude"]
    p1Longitude = p1["longitude"]
    p2Latitude = p2["latitude"]
    p2Longitude = p2["longitude"]
    # print("Calculando la distancia entre ({},{}) y ({},{})".format(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"]))
    earth_radius = {"km": 6371.0087714, "mile": 3959}
    result = earth_radius["km"] * acos(
        cos((radians(p1Latitude))) * cos(radians(p2Latitude)) * cos(radians(p2Longitude) - radians(p1Longitude)) + 
        sin(radians(p1Latitude)) * sin(radians(p2Latitude)))
    # print ("La distancia calculada es:{}".format(result))
    return result

def decode_polyline(polyline_str):
    """Pass a Google Maps encoded polyline string; returns list of lat/lon pairs"""
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates

def get_detailed_steps(steps):
    detailedSteps = []
    for step in steps:
        index = 0
        stepSpeed = (step["distance"]["value"] / 1000) / (step["duration"]["value"] / 3600)
        stepDistance = step["distance"]["value"]
        stepTime = step["duration"]["value"]
        try:
            stepManeuver = step["maneuver"]
        except:
            stepManeuver = "Straight"
        # Obtener polilínea
        substeps = decode_polyline(step["polyline"]["points"])
        for substep in substeps:
            if index < len(substeps):
                p1 = {"latitude": substeps[index][0], "longitude": substeps[index][1]}
                p2 = {"latitude": substeps[index + 1][0], "longitude": substeps[index + 1][1]}
                # Calcular distancia entre los dos puntos
                points_distance = distance(p1, p2) * 1000
                if points_distance > 1:
                    subStepDuration = points_distance / (stepSpeed / 3.6)
                    new_detailed_step = {"Origin": p1, "Destination": p2, "Speed": stepSpeed, "Time": subStepDuration,
                                         "Distance": points_distance, "Maneuver": stepManeuver}
                    detailedSteps.append(new_detailed_step)
    return detailedSteps

def getCommands(currentRouteDetailedSteps):
    global vehicleControlCommands
    steeringAngle: float = 90.0
    vehicleControlCommands = []
    index = 0
    for detailedStep in currentRouteDetailedSteps:
        index += 1
        # print("Generando el comando {} para el paso {}".format(index, detailedStep))
        if (detailedStep["Maneuver"].upper() == "STRAIGHT" or detailedStep["Maneuver"].upper() == "RAMP_LEFT"
                or detailedStep["Maneuver"].upper() == "RAMP_RIGHT" or detailedStep["Maneuver"].upper() == "MERGE"
                or detailedStep["Maneuver"].upper() == "MANEUVER_UNSPECIFIED"):
            steeringAngle = 90.0
        if detailedStep["Maneuver"].upper() == "TURN_LEFT":
            steeringAngle = 45.0
        if detailedStep["Maneuver"].upper() == "UTURN_LEFT":
            steeringAngle = 0.0
        if detailedStep["Maneuver"].upper() == "TURN_SHARP_LEFT":
            steeringAngle = 15.0
        if detailedStep["Maneuver"].upper() == "TURN_SLIGHT_LEFT":
            steeringAngle = 60.0
        if detailedStep["Maneuver"].upper() == "TURN_RIGHT":
            steeringAngle = 135.0
        if detailedStep["Maneuver"].upper() == "UTURN_RIGHT":
            steeringAngle = 180.0
        if detailedStep["Maneuver"].upper() == "TURN_SHARP_RIGHT":
            steeringAngle = 105.0
        if detailedStep["Maneuver"].upper() == "TURN_SLIGHT_RIGHT":
            steeringAngle = 150.0
        # Crear comando
        newCommand = {"SteeringAngle": steeringAngle, "Speed": detailedStep["Speed"], "Time": detailedStep["Time"]}
        vehicleControlCommands.append(newCommand)

def routes_manager(origin_address="Toronto", destination_address="Montreal"):
    global currentRouteDetailedSteps
    global vehicleControlCommands
    print("Asignando una ruta al vehículo...")
    url = "https://maps.googleapis.com/maps/api/directions/json?origin=" + origin_address + \
        "&destination=" + destination_address + "&key=" + google_maps_api_key
    # print("URL: {}".format(url))
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    current_route = response.text
    # print("La ruta es: {}".format(current_route))
    steps = response.json()["routes"][0]["legs"][0]["steps"]
    # print(steps)
    currentRouteDetailedSteps = get_detailed_steps(steps)
    getCommands(currentRouteDetailedSteps)
    print("Comandos asignados al vehículo")

def routes_loader(route):
    global routes
    new_route = json.loads(route)
    routes.append(new_route)

"""============= FUNCIONES DE CONTROL ============="""

def execute_command(command, step):
    global current_steering
    global current_speed
    global current_position
    global brake
    print(command)
    print()
    # Velocidad anterior
    last_speed = current_speed
    current_speed = command["Speed"]
    current_steering = command["SteeringAngle"]
    # Dividir el tiempo en intervalos de 0.5 segundos
    time_frames = command["Time"] / 0.1
    while time_frames > 0:
        # Parar si hay un obstáculo
        if current_obstacle_distance < 10:
            print("Obstáculo detectado a %.1f cm. Parando vehículo" % current_obstacle_distance)
            current_speed = 0
            brake = True
            time.sleep(0.1)
            continue
        else:
            current_speed = command["Speed"]
        # Frenar si la velocidad actual es menor que la anterior
        if current_speed < last_speed:
            brake = True
        else:
            brake = False
        # Actualizar tiempo restante
        time_frames -= 1
        time.sleep(0.1)

    # Actualizar la posición actual
    current_position = step["Destination"]
    
def vehicle_stop():
    global vehicleControlCommands
    global currentRouteDetailedSteps
    global current_steering
    global current_speed
    global current_leds
    global current_ldr
    global current_obstacle_distance

    # Detener el vehículo
    current_speed = 0
    current_ldr = 0
    current_steering = 90
    current_obstacle_distance = 0.0
    currentRouteDetailedSteps = []
    vehicleControlCommands = []
    current_leds_str = '[{"Color": "White", "Intensity": 0.0, "Blinking": "False"},' \
                        '{"Color": "White", "Intensity": 0.0, "Blinking": "False"},' \
                        '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"},' \
                        '{"Color": "Red", "Intensity": 0.0, "Blinking": "False"}]'
    current_leds = json.loads(current_leds_str)
    print("Vehículo detenido")

def vehicle_controller():
    global currentRouteDetailedSteps
    global vehicleControlCommands
    global routes

    while True:
        if len(routes) > 0:
            origin_address = routes[0]["Origin"]
            destination_address = routes[0]["Destination"]
            routes_manager(origin_address, destination_address)
            print("Número de comandos:", len(vehicleControlCommands))
            print("Comandos: {}".format(vehicleControlCommands))
            i = 0
            while len(vehicleControlCommands) > 0:
                print("Ejecutando comando %d:" % (i + 1))
                execute_command(vehicleControlCommands[0], currentRouteDetailedSteps[i])
                i += 1
                del vehicleControlCommands[0]
            if len(routes) > 0:
                del routes[0]
        else:
            print("No hay más rutas asignadas al vehículo")
            vehicle_stop()
            time.sleep(10)

def telemetry_manager():
    global current_speed
    global current_ldr
    global current_obstacle_distance
    global current_steering
    global current_position
    global current_leds

    while True:
        print("Velocidad actual: %.1f m/s" % current_speed)
        print("Luz ambiental: %.1f" % current_ldr)
        print("Distancia al obstáculo: %.1f cm" % current_obstacle_distance)
        print("Ángulo de dirección: %.1f grados" % current_steering)
        print("Luz delantera izquierda: {}".format(current_leds[0]))
        print("Luz delantera derecha: {}".format(current_leds[1]))
        print("Luz trasera izquierda: {}".format(current_leds[2]))
        print("Luz trasera derecha: {}".format(current_leds[3]))
        print("Posición actual: {}".format(current_position))
        print()
        time.sleep(2)

def start_vehicle():
    global t1, t2, t3, t4
    # Crear hilos
    t1 = threading.Thread(target=environment_simulator, daemon=True)
    t2 = threading.Thread(target=vehicle_controller, daemon=True)
    t3 = threading.Thread(target=led_manager, daemon=True)
    t4 = threading.Thread(target=telemetry_manager, daemon=True)
    # Iniciar hilos
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    # Esperar a que los hilos terminen
    t1.join()
    t2.join()
    t3.join()
    t4.join()


if __name__ == "__main__":
    try:
        # Cargar la ruta
        my_route = '{"Origin":"Aranjuez","Destination":"Ciempozuelos"}'
        routes_loader(my_route)

        # Iniciar vehículo
        start_vehicle()

    except Exception as e:
        print("Error: " + str(e))
        vehicle_stop()
        