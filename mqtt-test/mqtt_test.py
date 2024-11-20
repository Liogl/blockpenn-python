# packages: python-dotenv, paho-mqtt
# Publishing measurements
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import random  # Simulating sensor data, replace with actual sensor readings
import time

# Load .env.secret variables
from dotenv import dotenv_values
config = dotenv_values("../.env.secret")
config = dotenv_values(".env.secret")

# MQTT configuration
BROKER = config["BROKER"]
PORT = config["PORT"]
TOPIC = config["TOPIC"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
TOPIC2 = "home/rpi/1/availability"

# Make PORT an integer and generate an error if it's not
try:
    port_int = int(PORT)
except ValueError:
    print("Invalid input. Please enter a valid integer.")

def generate_measurements():
    """Simulate or collect actual sensor measurements."""
    return {
        "temperature": round(random.uniform(20.0, 30.0), 2),  # Simulate temperature in Celsius
        "humidity": round(random.uniform(30.0, 70.0), 2),  # Simulate humidity in percentage
        "timestamp": datetime.now().isoformat(),  # Current timestamp in ISO 8601 format
        "pm1": round(random.uniform(5.0, 15.0), 2)  # Simulate PM1 concentration in µg/m³
    }

# reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
def on_publish(client, userdata, mid, reason_code, properties):
    try:
        userdata.remove(mid)
    except KeyError:
        print("Message ID not found in unacked_publish set")
        
unacked_publish = set()
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

mqttc.user_data_set(unacked_publish)
mqttc.username_pw_set(USERNAME, PASSWORD)
mqttc.connect(BROKER, port_int, 60)
mqttc.loop_start()

measurements = generate_measurements()
payload = json.dumps(measurements)

# Our application produce some messages
msg_info = mqttc.publish(TOPIC, payload, retain=True)
msg_info.is_published()
# unacked_publish.add(msg_info.mid)

msg_info2 = mqttc.publish("paho/test/topic", "my message2", qos=1)
unacked_publish.add(msg_info2.mid)

# # Wait for all message to be published
# while len(unacked_publish):
#     time.sleep(0.1)

# Due to race-condition described above, the following way to wait for all publish is safer
msg_info.wait_for_publish()
msg_info2.wait_for_publish()

mqttc.disconnect()
mqttc.loop_stop()
