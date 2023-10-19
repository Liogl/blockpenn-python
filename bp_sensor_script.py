#!/usr/bin/python
import math, struct, array, time, io, fcntl
import logging, os, inspect, logging.handlers
import board
import adafruit_shtc3
import Adafruit_SSD1306
## SPS30
from SPS30 import sps30
## SPS30
## T6713
from T6713 import t6713
## T6713
import influxdb_utils

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# for the leds and buttons
import RPi.GPIO as GPIO # Import RPi.GPIO library

LED1_PIN = 23 # red 
LED2_PIN = 22 # green

LBTN_PIN = 27 # pull-down - Not working. Design connects it ground the RPI GPIO.
MBTN_PIN = 17 # pull-down
RBTN_PIN = 4  # pull-down

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

# Panels
PANEL_NUM = 3
PANEL_DELAY = 30 # In seconds
cur_panel = 1

# DB
DB_SAMPLE_PERIOD = 10 # Write the samples to the DB every DB_SAMPLE_PERIOD seconds

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

# Set the leds & btns
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

# T6713 start


# T6713 end

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

# Connect SHTC3
i2c = board.I2C()  # uses board.SCL and board.SDA
sht = adafruit_shtc3.SHTC3(i2c)

# Connect T6713
## T6713
obj_6713 = t6713.T6713()
## T6713

## SPS30
sps = sps30.SPS30()
print(f'SPS30 Firmware Version: {sps.firmware_version()}')
print(f'SPS30 Product Type: {sps.product_type()}')
print(f'SPS30 Device Serial: {sps.serial_number()}')
print(f"SPS30 Status Register: {sps.read_status_register()}")
print(f'SPS30 Auto cleaning Interval: {sps.read_auto_cleaning_interval()}')
sps.reset()
time.sleep(1)
sps.start_measurement()

# Configure the display panel
def showPanel(panel_id):
	try:
		draw.text((x, top    ), "- "+str(panel_id)+" -", font=font, fill=255)
		if (panel_id == 0):
			draw.text((x, top+8*1), "SYSTEM STATS",  font=font, fill=255)
			draw.text((x, top+8*2), "IP: " + str(IP.decode('utf-8')),  font=font, fill=255)
			draw.text((x, top+8*3), str(CPU.decode('utf-8')), font=font, fill=255)
			draw.text((x, top+8*4), str(MemUsage.decode('utf-8')),  font=font, fill=255)
			draw.text((x, top+8*5), str(Disk.decode('utf-8')),  font=font, fill=255)
		if (panel_id == 1):
			draw.text((x, top+8*1), "SENSORS: Tmp, Hum, CO2",  font=font, fill=255)
			draw.text((x, top+8*2), "SHTC3",  font=font, fill=255)
			draw.text((x, top+8*3), str("Temperature: %0.1f C" % temperature),  font=font, fill=255)
			draw.text((x, top+8*4), str("Humidity: %0.1f %%" % relative_humidity),  font=font, fill=255)
## T6713
			draw.text((x, top+8*5), "T6713 (Status:"+str(bin(obj_6713.status())+")"),  font=font, fill=255)
			draw.text((x, top+8*6), str("PPM: "+str(obj_6713.gasPPM())),  font=font, fill=255)
			draw.text((x, top+8*7), str("ABC State: "+str(obj_6713.checkABC())),  font=font, fill=255)
## T6713
		if (panel_id == 2):
			draw.text((x, top+8*1), "SENSORS: Air Quality",  font=font, fill=255)
			sps_values = json.dumps(sps.get_measurement(), indent=2)
## SPS30	
			draw.text((x, top+8*2), str("PM1.0: %0.1f µg/m3" % sps_values['sensor_data']['mass_density']['pm1.0']),  font=font, fill=255)
			draw.text((x, top+8*3), str("PM2.5: %0.1f µg/m3" % sps_values['sensor_data']['mass_density']['pm2.5']),  font=font, fill=255)
			draw.text((x, top+8*4), str("PM10 : %0.1f µg/m3" % sps_values['sensor_data']['mass_density']['pm10']),  font=font, fill=255)
			draw.text((x, top+8*5), str("NC1.0: %0.1f 1/cm3" % sps_values['sensor_data']['particle_count']['pm1.0']),  font=font, fill=255)
			draw.text((x, top+8*6), str("NC4.0: %0.1f 1/cm3" % sps_values['sensor_data']['particle_count']['pm4.0']),  font=font, fill=255)
			draw.text((x, top+8*7), str("Typical Particle Size: %0.1f µm" % sps_values['sensor_data']['particle_size']),  font=font, fill=255)
## SPS30
	except Exception as e:
		green_led.set_led(0)
		# GPIO.cleanup()
		logging.exception("main crashed during panel display. Error: %s", e)

def saveResults():
    while True:
        if sps.read_data_ready_flag():
            break
    sps_values = sps.get_measurement() #json.dumps(sps.get_measurement(), indent=2)
    data = {
        "Temperature" : float(temperature),
        "Humidity" : float(relative_humidity),
        "CO2 Concentration" : float(obj_6713.gasPPM()),
        "CO2 ABC State" : float(obj_6713.checkABC()),
        "AQ_PM1.0" : float(sps_values['sensor_data']['mass_density']['pm1.0']),
        "AQ_PM2.5" : float(sps_values['sensor_data']['mass_density']['pm2.5']),
        "AQ_PM4" : float(sps_values['sensor_data']['mass_density']['pm4.0']),
        "AQ_PM10" : float(sps_values['sensor_data']['mass_density']['pm10']),
        "AQ_NC0_5" : float(sps_values['sensor_data']['particle_count']['pm0.5']),
        "AQ_NC1" : float(sps_values['sensor_data']['particle_count']['pm1.0']),
        "AQ_NC2_5" : float(sps_values['sensor_data']['particle_count']['pm2.5']),
        "AQ_NC4" : float(sps_values['sensor_data']['particle_count']['pm4.0']),
        "AQ_NC10" : float(sps_values['sensor_data']['particle_count']['pm10']),
        "AQ_NC0_TYPICAL" : float(sps_values['sensor_data']['particle_size'])
    }
    
    influxdb_utils.influx_write(data)
## SPS30

# Global vars
cmd = "hostname -I | cut -d\' \' -f1"
IP = subprocess.check_output(cmd, shell = True )
cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
CPU = subprocess.check_output(cmd, shell = True )
cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
MemUsage = subprocess.check_output(cmd, shell = True )
cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
Disk = subprocess.check_output(cmd, shell = True )
temperature, relative_humidity = sht.measurements

def main():
	global IP, CPU, MemUsage, Disk, temperature, relative_humidity, obj_6713, sps, cur_panel
	green_led_status = 1
	db_sample_start = time.time()
	panel_start = time.time()
	str_panel_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(panel_start))
	print(str_panel_start+": main started")
	while True:
		# Blink the green led
		logging.debug('green_led_status'+str(green_led_status))
		green_led.set_led(green_led_status)
		green_led_status = 0 if green_led_status else 1 
		
		# Draw a black filled box to clear the image.
		draw.rectangle((0,0,width,height), outline=0, fill=0)

		# Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
		cmd = "hostname -I | cut -d\' \' -f1"
		IP = subprocess.check_output(cmd, shell = True )
		cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
		CPU = subprocess.check_output(cmd, shell = True )
		cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
		MemUsage = subprocess.check_output(cmd, shell = True )
		cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
		Disk = subprocess.check_output(cmd, shell = True )

		# Get measurements
		temperature, relative_humidity = sht.measurements
## SPS30
		logging.debug('Reading SPS30 data')		
		# if not sps.read_data_ready_flag():
		# 	print(sps.read_data_ready_flag())
		# 	raise Exception("SPS30: read_data_ready_flag raised exception")		
## SPS30

		# Set display
		if (time.time()-panel_start > PANEL_DELAY):
			cur_panel = (cur_panel+1) % PANEL_NUM
			panel_start = time.time()
		showPanel(cur_panel)

		# Write measurements to the DB
		if (time.time()-db_sample_start > DB_SAMPLE_PERIOD):
			logging.debug('Writing samples to the DB')
			saveResults()
			db_sample_start = time.time()
		
		# Display image.
		disp.image(image)
		disp.display()
		time.sleep(1)

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		green_led.set_led(0)
		# red_led.set_led(1)
		GPIO.cleanup()
		logging.exception("main crashed. Error: %s", e)
