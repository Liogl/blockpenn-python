##Imports
import math, struct, array, time, io, fcntl, datetime
import logging, os, inspect, logging.handlers
import board
#AWS Imports
from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import time
import json
import random
from AWSHandler.functions import on_connection_interrupted, on_connection_resumed, on_resubscribe_complete, on_message_received, on_connection_success, on_connection_failure, on_connection_closed

#Power and Energy Readings: Kasa
from Kasa import KasaHandler
from dotenv import load_dotenv
#Temperature and Humidity Sensor: SHTC3
import adafruit_shtc3
#Particulate MAtter Sensor: SPS30
from SPS30.i2c import SPS30_I2C
#CO2 Sensor: T6713
from T6713 import t6713
#OLED: SSD1306
import Adafruit_SSD1306
#OLED Utils
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import RPi.GPIO as GPIO

load_dotenv("../Certificates/Kasa.env")

LED1_PIN = 23 # red 
LED2_PIN = 22 # green

LBTN_PIN = 27 # pull-down - Not working. Design connects it ground the RPI GPIO.
MBTN_PIN = 17 # pull-down
RBTN_PIN = 4  # pull-down

DB_SAMPLE_PERIOD = 10 # Write the samples to the DB every DB_SAMPLE_PERIOD seconds

# Device Data Fn
def get_device_data():
    
    # Extract the IP address of the host
	cmd = "hostname -I | cut -d\' \' -f1"
	IP = subprocess.check_output(cmd, shell = True)
	# Retrieves CPU load information using the top -bn1 command, filters the output to 
	# include only lines with "load" using grep, and then uses awk to print the CPU load 
	# value in a formatted manner.
	cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
	CPU_load = subprocess.check_output(cmd, shell = True)
	# Retrieves memory usage information using the free -m command, then processes 
	# the output using awk to calculate and print the used memory, total memory, and usage percentage
	cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
	memory_usage = subprocess.check_output(cmd, shell = True)
	# Retrieves disk usage information using the df -h command and then processes the 
 	# output using awk to print the used and total disk space along with the usage percentage
	cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
	disk_usage = subprocess.check_output(cmd, shell = True)
 
	device_data = {
		"IP Address": str(IP.decode('utf-8')), 
        "CPU Load": CPU_load.decode('utf-8').split(': ')[1],
        "Memory Usage": memory_usage.decode('utf-8').split(': ')[1],
        "Disk Usage": disk_usage.decode('utf-8').split(': ')[1]
	}
	
	return device_data

##Logging Init
# Start logging
log_fname = os.path.splitext(os.path.basename(__file__))[0]+".log"
log_level = logging.DEBUG

logger = logging.getLogger('MyLogger')
logger.setLevel(log_level)

# Adding rotating log
log_handler = logging.handlers.RotatingFileHandler(
	log_fname,
	maxBytes=200000, 
	backupCount=5)
logger.addHandler(log_handler)

logging.basicConfig(
	handlers=[log_handler],
	format='%(asctime)s [%(levelname)-8s] %(message)s',
	level=log_level,
	datefmt='%Y-%m-%d %H:%M:%S')
logger.debug('Script started')

#GPIO Setup
# Start the lgpio
GPIO.setwarnings(False) # Ignore warning (TBD)
GPIO.setmode(GPIO.BCM) # Use BCM instead of physical mapping

# GPIO classes: led & btn
class led:
	global GPIO
	def __init__(self, led_pin, callback=None):
		GPIO.setup(led_pin, GPIO.OUT)
		self.led_pin = led_pin

	def set_led(self, state):
		GPIO.output(self.led_pin, state)

class btn:
	global GPIO
	def __init__(self, btn_pin, callback=None):
		GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
		GPIO.add_event_detect(btn_pin,GPIO.FALLING,callback=callback) 
		self.btn_pin = btn_pin


def button_callback(channel):
	global cur_panel
	logging.info("Button was pushed! (GPIO "+str(channel)+")")
	if (channel == LBTN_PIN) : 
		if (cur_panel > 0): cur_panel = (cur_panel-1) % PANEL_NUM
		else : cur_panel = PANEL_NUM - 1
	if channel == RBTN_PIN: cur_panel = (cur_panel+1) % PANEL_NUM

logging.info('Setting leds and buttons')
red_led = led(LED1_PIN, 0)
green_led = led(LED2_PIN, 0)
l_btn = btn(LBTN_PIN, callback=button_callback)
r_btn = btn(RBTN_PIN, callback=button_callback)
logging.info('Completed setting leds and buttons')
green_led.set_led(1)

red_led.set_led(1)
time.sleep(1)
red_led.set_led(0)

##OLED Setup
# Panels
PANEL_NUM = 3
PANEL_DELAY = 30 # In seconds
cur_panel = 1
# Raspberry Pi pin configuration:
logging.debug('OLED set up')
RST = None     # on the PiOLED this pin isnt used
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
# Initialize library.
try:
	disp.begin()
except Exception as e:
	logging.exception("Main crashed during OLED setup. Error: %s", e)
	  
# Clear display.
disp.clear()
disp.display()

def showPanel(panel_id):
	try:
		data = getData()
		draw.text((x, top    ), "- "+str(panel_id)+" -", font=font, fill=255)
		if (panel_id == 0):
			draw.text((x, top+8*1), "SYSTEM STATS",  font=font, fill=255)
			draw.text((x, top+8*2), "IP: " + str(data["IP Address"]),  font=font, fill=255)
			draw.text((x, top+8*3), str(data["CPU Load"]), font=font, fill=255)
			draw.text((x, top+8*4), str(data["Memory Usage"]),  font=font, fill=255)
			draw.text((x, top+8*5), str(data["Disk Usage"]),  font=font, fill=255)
		if (panel_id == 1):
			draw.text((x, top+8*1), "SENSORS: Tmp, Hum, CO2",  font=font, fill=255)
			draw.text((x, top+8*2), "SHTC3",  font=font, fill=255)
			draw.text((x, top+8*3), str("Temperature: %0.1f C" % data["Temperature"]),  font=font, fill=255)
			draw.text((x, top+8*4), str("Humidity: %0.1f %%" % data["Humidity"]),  font=font, fill=255)
## T6713
			draw.text((x, top+8*5), "T6713 (Status:"+str(data["CO2 Sensor Status"])+")",  font=font, fill=255)
			draw.text((x, top+8*6), str("PPM: "+str(data["CO2 Concentration"])),  font=font, fill=255)
			draw.text((x, top+8*7), str("ABC State: "+str(data["CO2 ABC State"])),  font=font, fill=255)
## T6713
		if (panel_id == 2):
			draw.text((x, top+8*1), "SENSORS: Air Quality",  font=font, fill=255)
## SPS30	
			draw.text((x, top+8*2), str("PM1.0: %0.1f µg/m3" % data["pm10 standard"]),  font=font, fill=255)
			draw.text((x, top+8*3), str("PM2.5: %0.1f µg/m3" % data["pm25 standard"]),  font=font, fill=255)
			draw.text((x, top+8*4), str("PM10 : %0.1f µg/m3" % data["pm100 standard"]),  font=font, fill=255)
			draw.text((x, top+8*5), str("NC1.0: %0.1f 1/cm3" % data["particles 10um"]),  font=font, fill=255)
			draw.text((x, top+8*6), str("NC4.0: %0.1f 1/cm3" % data["particles 40um"]),  font=font, fill=255)
			draw.text((x, top+8*7), str("Typical Particle Size: %0.1f µm" % data["tps"]),  font=font, fill=255)
## SPS30
	except Exception as e:
		green_led.set_led(0)
		# GPIO.cleanup()
		logging.exception("main crashed during panel display. Error: %s", e)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()

##SHTC3 Setup
# Connect SHTC3
i2c = board.I2C()  # uses board.SCL and board.SDA
sht = adafruit_shtc3.SHTC3(i2c)

##T6713 Setup
obj_6713 = t6713.T6713()

##SPS30 Setup
sps = SPS30_I2C(i2c)

##Kasa Setup
kasa_username = os.environ.get("USERNAME")
kasa_password = os.environ.get("PASSWORD")
kasaObject = KasaHandler.Kasa()
uuid = kasaObject.create_random_uuid()
response_code = kasaObject.set_auth_token(uuid, kasa_username, kasa_password)
[response_code, err_code, dev_list] = kasaObject.get_set_dev_list()
response_code = kasaObject.handle_devices(2)

##AWS Setup
# Create the proxy options if the data is present in cmdData
proxy_options = None

##Certificates Directory - Find Keys
# auth_paths[0] : Thing Certificate
# auth_paths[1] : Private Key
# auth_paths[2] : CA1 General Certificate 
# auth_paths[3] : Thing Identifier
certificates_path = "../Certificates"
auth_paths = [None]*4
for file_path in os.listdir(certificates_path):
    if file_path.endswith("-certificate.pem.crt"):
        auth_paths[0] = os.path.join(certificates_path, file_path)
    elif file_path.endswith("-private.pem.key"):
        auth_paths[1] = os.path.join(certificates_path, file_path)
        auth_paths[3] = file_path.split("-")[0]
    elif file_path.endswith("CA1.pem"):
        auth_paths[2] = os.path.join(certificates_path, file_path)

# Create a MQTT connection from the command line data
mqtt_connection = mqtt_connection_builder.mtls_from_path(
	endpoint="a3cp1px06xaavc-ats.iot.us-east-1.amazonaws.com",
	cert_filepath = auth_paths[0],
	pri_key_filepath = auth_paths[1],
	ca_filepath = auth_paths[2],
	on_connection_interrupted=on_connection_interrupted,
	on_connection_resumed=on_connection_resumed,
	client_id=auth_paths[3],
	clean_session=False,
	keep_alive_secs=30,
	http_proxy_options=proxy_options,
	on_connection_success=on_connection_success,
	on_connection_failure=on_connection_failure,
	on_connection_closed=on_connection_closed)

connect_future = mqtt_connection.connect()
# Future.result() waits until a result is available
connect_future.result()
print("Connected!")

def getData():
     
	device_data = get_device_data()
	temperature, relative_humidity = sht.measurements
	data = {
		"Timestamp": datetime.datetime.now().timestamp(),
		"RPI Identifier": auth_paths[3],
        "Temperature" : float(temperature),
        "Humidity" : float(relative_humidity),
        "CO2 Sensor Status" : str(obj_6713.status()),
        "CO2 Concentration" : float(obj_6713.gasPPM()),
        "CO2 ABC State" : float(obj_6713.checkABC())
    }
	kasa_data = kasaObject.get_power_energy_data()
	{data.update(plug_data) for _, plug_data in kasa_data.items()}
	data.update(sps.read())
	data.update(device_data)
	return data

def publishData():
    data = getData()
    message_json = json.dumps(data)
    mqtt_connection.publish(
		topic="data/measurement",
		payload=message_json,
		qos=mqtt.QoS.AT_LEAST_ONCE)

        
if __name__ == "__main__":
	try:
		green_led_status = 1
		db_sample_start = time.time()
		oled_panel_start = time.time()
		print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(oled_panel_start))}: main started")
		draw.rectangle((0, 0, width, height), outline=0, fill=0)


		while True:
			green_led_status ^= 1
			logging.debug(f'green_led_status{green_led_status}')
			green_led.set_led(green_led_status)
			draw.rectangle((0,0,width,height), outline=0, fill=0)
			if time.time() - oled_panel_start > PANEL_DELAY:
				cur_panel = (cur_panel + 1) % PANEL_NUM
				oled_panel_start = time.time()
			showPanel(cur_panel)
        
			if time.time() - db_sample_start > DB_SAMPLE_PERIOD:
				logging.debug('Writing samples to the DB')
				publishData()
				db_sample_start = time.time()

			disp.image(image)
			disp.display()
			time.sleep(1)

	except Exception as e: 
		print(e)
		# Disconnect
		print("Disconnecting...")
		disconnect_future = mqtt_connection.disconnect()
		disconnect_future.result()
		print("Disconnected!")
