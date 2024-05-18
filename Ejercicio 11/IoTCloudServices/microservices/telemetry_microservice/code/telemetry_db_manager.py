import mysql.connector
import os

def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DBHOST'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )
    return mydb

def register_new_telemetry(params):
    mydb = connect_database()
    sql = "INSERT INTO vehicles_telemetry (vehicle_id, current_steering, current_speed, latitude, longitude, \
    current_ldr, current_obstacle_distance, front_left_led_intensity, front_right_led_intensity, \
    rear_left_led_intensity, rear_right_led_intensity, front_left_led_color, front_right_led_color, \
    rear_left_led_color, rear_right_led_color, front_left_led_blinking, front_right_led_blinking, \
    rear_left_led_blinking, rear_right_led_blinking, time_stamp) VALUES \
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s));"

    latitude = params["current_position"]["latitude"]
    longitude = params["current_position"]["longitude"]

    front_left_led_intensity = params["current_leds"][0]["Intensity"]
    front_right_led_intensity = params["current_leds"][1]["Intensity"]
    rear_left_led_intensity = params["current_leds"][2]["Intensity"]
    rear_right_led_intensity = params["current_leds"][3]["Intensity"]
    front_left_led_color = params["current_leds"][0]["Color"]
    front_right_led_color = params["current_leds"][1]["Color"]
    rear_left_led_color = params["current_leds"][2]["Color"]
    rear_right_led_color = params["current_leds"][3]["Color"]
    front_left_led_blinking = params["current_leds"][0]["Blinking"]
    front_right_led_blinking = params["current_leds"][1]["Blinking"]
    rear_left_led_blinking = params["current_leds"][2]["Blinking"]
    rear_right_led_blinking = params["current_leds"][3]["Blinking"]
    
    query_params = (params['vehicle_id'], params['current_steering'], params['current_speed'], latitude, longitude, \
    params['current_ldr'], params['current_obstacle_distance'], front_left_led_intensity, front_right_led_intensity, \
    rear_left_led_intensity, rear_right_led_intensity, front_left_led_color, front_right_led_color, \
    rear_left_led_color, rear_right_led_color, front_left_led_blinking, front_right_led_blinking, \
    rear_left_led_blinking, rear_right_led_blinking, params['time_stamp'])
    
    with mydb.cursor() as mycursor:
        try:
            mycursor.execute(sql, query_params)
            mydb.commit()
            return True
        except Exception as e:
            print("Error inserting new telemetry record:", e)
            return False

def get_vehicle_detailed_info(params):
    mydb = connect_database()
    result = []
    sql = "SELECT vehicle_id, current_steering, current_speed, current_ldr, \
        current_obstacle_distance, front_left_led_intensity, front_right_led_intensity, \
        rear_left_led_intensity, rear_right_led_intensity, front_left_led_color, \
        front_right_led_color, rear_left_led_color, rear_right_led_color, \
        front_left_led_blinking, front_right_led_blinking, rear_left_led_blinking, \
        rear_right_led_blinking, time_stamp FROM vehicles_telemetry \
        WHERE vehicle_id = %s ORDER BY time_stamp LIMIT 20"
    query_params = (params['vehicle_id'],)
    with mydb.cursor() as mycursor:
        try:
            mycursor.execute(sql, query_params)
            my_result = mycursor.fetchall()
            for vehicle_id, current_steering, current_speed, current_ldr, \
                current_obstacle_distance, front_left_led_intensity, \
                front_right_led_intensity, rear_left_led_intensity, \
                rear_right_led_intensity, front_left_led_color, \
                front_right_led_color, rear_left_led_color, rear_right_led_color, \
                front_left_led_blinking, front_right_led_blinking, \
                rear_left_led_blinking, rear_right_led_blinking, time_stamp in my_result:
                item = {"Vehicle_id": vehicle_id, 
                        "Current Steering": current_steering, 
                        "Current Speed": current_speed, 
                        "Current LDR": current_ldr, 
                        "Obstacle Distance":current_obstacle_distance, 
                        "Front Left Led Intensity": front_left_led_intensity, 
                        "Front Right Led Intensity": front_right_led_intensity, 
                        "Rear Left Led Intensity": rear_left_led_intensity, 
                        "Rear Right Led Intensity": rear_right_led_intensity, 
                        "Front Left Led Color": front_left_led_color, 
                        "Front Right Led Color": front_right_led_color, 
                        "Rear Left Led Color": rear_left_led_color, 
                        "Rear Right Led Color": rear_right_led_color, 
                        "Front Left Led Blinking": front_left_led_blinking, 
                        "Front Right Led Blinking": front_right_led_blinking, 
                        "Rear Left Led Blinking": rear_left_led_blinking, 
                        "Rear Right Led Blinking": rear_right_led_blinking, 
                        "Time Stamp": time_stamp}
                result.append(item)
            mydb.commit()    
            return {"Vehicle Detailed Info": result, "Error Message": None}
        except Exception as e:
            print("Error getting vehicle detailed info:", e)
            return {"Error Message": "Error getting vehicle detailed info"}
        
def get_vehicles_last_position():
    mydb = connect_database()
    result = []
    sql = "SELECT vehicles.vehicle_id, plate, latitude, longitude, time_stamp FROM vehicles, \
        vehicles_telemetry WHERE vehicles.vehicle_id=vehicles_telemetry.vehicle_id AND \
        status = 1 AND time_stamp=(SELECT MAX(time_stamp) FROM vehicles_telemetry)"
    with mydb.cursor() as my_cursor:
        try:
            my_cursor.execute(sql)
            my_result = my_cursor.fetchall()
            for vehicle_id, plate, latitude, longitude, time_stamp in my_result:
                item = {"Vehicle_id": vehicle_id, "Plate": plate, "Latitude": latitude, 
                        "Longitude": longitude, "Time Stamp": time_stamp}
                result.append(item)
            mydb.commit()
            return {"Vehicle Last Position": result, "Error Message": None}
        except Exception as e:
            print("Error getting vehicles last position:", e)
            return {"Error Message": "Error getting vehicles last position"}
        