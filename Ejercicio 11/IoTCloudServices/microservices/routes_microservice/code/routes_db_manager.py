import mysql.connector
import os
import datetime

def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DBHOST'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )
    return mydb

def assign_new_route(params):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = "INSERT INTO routes (origin, destination, status, plate, time_stamp) VALUES (%s, %s, %s, %s, %s)"
        vehicle_plate = params["plate"]
        origin = params["origin"]
        destination = params["destination"]
        time_stamp = datetime.datetime.now()
        state = "Sent"
        tuples = (origin, destination, state, vehicle_plate, time_stamp)
        try:
            mycursor.execute(sql, tuples)
            mydb.commit()
            print(mycursor.rowcount, "Route inserted.")
            return True
        except Exception as e:
            print("Error inserting a route", e)
            return False

def get_routes_assigned_to_vehicle(vehicle):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = "SELECT * FROM routes WHERE plate = %s"
        vehicle_plate = vehicle["plate"]
        mycursor.execute(sql, (vehicle_plate,))
        myresult = mycursor.fetchall()
        routes = []
        for route in myresult:
            routes.append({"origin": route[1],
                           "destination": route[2],
                           "status": route[3],
                           "time_stamp": route[4]})
        mydb.commit()
        return routes

def register_delivered_route():
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = "UPDATE routes SET status = 'Delivered' ORDER BY time_stamp DESC LIMIT 1;"
        try:
            mycursor.execute(sql)
            mydb.commit()
            print(mycursor.rowcount, "Route updated.")
            return True
        except:
            print("Error updating the route")
            return False

def register_completed_route(params):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = ("UPDATE routes SET status = 'Completed' WHERE plate = %s AND status != 'Completed' "
               "ORDER BY time_stamp ASC LIMIT 1;")
        vehicle_plate = params["Plate"]
        try:
            mycursor.execute(sql, (vehicle_plate,))
            mydb.commit()
            print(mycursor.rowcount, "Route updated.")
            return True
        except:
            print("Error updating the route")
            return False
        