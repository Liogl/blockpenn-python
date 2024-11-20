from influxdb import InfluxDBClient
from datetime import datetime
import logging
#import time

# DB Variables
DB_VAR_IP = '127.0.0.1'
DB_VAR_PORT = 8086
DB_VAR_USER = 'root'
DB_VAR_PASS = 'root' #open('/home/ubuntu/bp_data/node/influxdb_authdata/user_password', 'r').read() #'root'
DB_VAR_DB_NAME = 'db0' #'Meyerson_Deployment'

def createDatabase():
    client = InfluxDBClient(DB_VAR_IP, DB_VAR_PORT, DB_VAR_USER, DB_VAR_PASS, DB_VAR_DB_NAME)
    client.create_database(DB_VAR_DB_NAME)
    # set retention policy to 30 days
    client.create_retention_policy(name='30_days', duration='30d', replication=1, database=DB_VAR_DB_NAME, default=True)
    return client

client = createDatabase()

def ganacheLogger(data, Measurement, Unit, MAC_Address, unit_descrip, sensor_name, mfg_name):
    global client
    # This is per data Transmission
    json_body = []
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    json_body.append(
        {
            "measurement": Measurement,         # CO2, Temp, etc 
            "tags": {
                "ProjectID": "“BlockPenn”",            # CharacterString, project identifier, eg. “BlockPenn”
                "ProjectDeployment": "Deployment 1",        # CharacterString, phase of the project
                "UnitDescription": unit_descrip,        # CharacterString, e.g. "degree Celsius"
                "UnitSymbol": Unit,        # CharacterString, e.g. "°C"
                "MACAddress": MAC_Address,            # CharacterString
                "TimeZone": "Philadelphia",            # CharacterString
                "Address": "Lior test addr",                 # CharacterString
                "BuildingID": "N/A",                   # CharacterString
                "BuildingName": "Lior test RPi",               # CharacterString
                "RoomNumber": "Lior test room",       # CharacterString
                "SensorName": sensor_name,               # CharacterString, eg. DHT22
                "SensorManufacturer": mfg_name        # CharacterString, company name
            },
            "LocalTime": current_time,              # TM_Instant (ISO 8601 Time string) '%Y-%m-%dT%H:%M:%SZ' 
            "fields": {
                "value": data           # Any
            }
        }
    )
    client.write_points(json_body)
#    print("Wrote data point for:", Measurement, " as: ", data)
