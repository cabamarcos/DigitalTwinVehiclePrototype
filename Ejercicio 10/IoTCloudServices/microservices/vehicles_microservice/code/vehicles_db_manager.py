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

def get_active_vehicles():
    mydb = connect_database()
    plates = []
    sql = "SELECT plate FROM vehicles WHERE status = 1 ORDER BY plate;"
    with mydb.cursor() as mycursor:
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        for plate in myresult:
            data = {"Plate": plate[0]}
            plates.append(data)
        mydb.commit()
    return plates

def register_new_vehicle(vehicle):
    vehicle_plate = ""
    mydb = connect_database()

    sql = "SELECT plate FROM vehicles WHERE vehicle_id = %s ORDER BY plate ASC LIMIT 1;"
    with mydb.cursor() as mycursor:
        mycursor.execute(sql, (vehicle['vehicle_id'],))
        myresult = mycursor.fetchall()
        for plate in myresult:
            vehicle_plate = plate
        mydb.commit()
    # Matricula ya asignada
    if vehicle_plate != "":
        print("Matricula ya asignada:", vehicle_plate)
        # Actualizar estado del vehículo
        sql = "UPDATE vehicles SET status = 1 WHERE vehicle_id = %s;"
        with mydb.cursor() as mycursor:
            try:
                mycursor.execute(sql, (vehicle["vehicle_id"],))
                mydb.commit()
                print(mycursor.rowcount, "record updated.")
                return vehicle_plate[0]
            except:
                print("Error updating record.")
                return ""
    # Matricula no asignada
    else:
        sql = "SELECT plate, is_assigned FROM available_plates WHERE is_assigned = 0 ORDER BY plate ASC LIMIT 1;"
        with mydb.cursor() as mycursor:
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            for plate in myresult:
                vehicle_plate = plate
            mydb.commit()

        print("Matricula disponible", vehicle_plate)

        # Matricula disponible en available plates
        if vehicle_plate != "":
            with mydb.cursor() as mycursor:
                sql = "INSERT INTO vehicles (vehicle_id, plate, status) VALUES (%s, %s, 1);"
                query_params = (vehicle['vehicle_id'], vehicle_plate[0])
                try:
                    mycursor.execute(sql, query_params)
                    mydb.commit()
                    print(mycursor.rowcount, "record inserted.")
                    sql = "UPDATE available_plates SET is_assigned = 1 WHERE plate = %s;"
                    mycursor.execute(sql, (vehicle_plate[0],))
                    mydb.commit()
                    print(mycursor.rowcount, "record updated.")
                    return vehicle_plate[0]
                except:
                    print("Error inserting record.")
                    return ""
        # Matricula no disponible en available plates
        else:
            print("No plates available.")
            return ""

def deactivate_vehicle(vehicle):
    mydb = connect_database()
    sql = "UPDATE vehicles SET status = 0 WHERE vehicle_id = %s;"
    with mydb.cursor() as mycursor:
        try:
            mycursor.execute(sql, (vehicle["vehicle_id"],))
            mydb.commit()
            print(mycursor.rowcount, "record updated.")
            return True
        except Exception as e:
            print("Error updating record.", e)
            return False
