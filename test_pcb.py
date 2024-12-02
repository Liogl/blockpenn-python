# This is a code aimed to test the PCB
# Requires: sudo python3 -m pip install simple-term-menu

#!/usr/bin/env python3

#TODO: 
# T6713
# OLED
# Clean old code

from simple_term_menu import TerminalMenu
import logging, os, inspect, logging.handlers
import math, struct, array, time, io, fcntl
import RPi.GPIO as GPIO # Import RPi.GPIO library
import board

# GPIO setup: un/comment based on PCB version 
# PCB V2
# LED1_PIN = 23 # red 
# LED2_PIN = 22 # green

# LBTN_PIN = 27 # pull-down - Not working. Design connects it ground the RPI GPIO.
# MBTN_PIN = 17 # pull-down
# RBTN_PIN = 4  # pull-down

# PCB V1
LED1_PIN = 22 # red 
LED2_PIN = 23 # green

LBTN_PIN = 4 # Bottom, pull-down
RBTN_PIN = 27 # Into the center of the PCB, pull-down

# Set all legacy loggers to ERROR
# Get the root logger
root_logger = logging.getLogger()

# Iterate over all loggers
for logger_name in logging.root.manager.loggerDict:
	logger = logging.getLogger(logger_name)
	logger.setLevel(logging.ERROR)

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

class bcolors:
	TEXT = '\033[0m'
	PASS = '\033[32m'
	WARN = '\033[33m'
	FAIL = '\033[31m'
	HIGH = '\033[36m'

# Start the lgpio
def gpio_start():
	# for the leds and buttons
	global GPIO 
	GPIO.setwarnings(False) # Ignore warning (TBD)
	GPIO.setmode(GPIO.BCM) # Use BCM instead of physical mapping
	global i2c 
	i2c = board.I2C()  # uses board.SCL and board.SDA

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
	print("Button was pushed! (GPIO "+str(channel)+")")

def test(comp_test):
	res_test = False

	if comp_test == "SHTC3":
		try: 
			test_shtc3()
			res_test = True
		except: res_test = False
	elif comp_test == "SPS30":
		try: 
			test_sps30()
			res_test = True
		except: res_test = False
	elif comp_test == "T6713":
		try: 
			test_t6713()
			res_test = True
		except: res_test = False
	elif comp_test == "OLED":
		try: 
			test_oled()
			res_test = True
		except: res_test = False
	else:
		print("Error: could not find component function")

	return res_test

def test_shtc3():
	# Connect SHTC3
	import adafruit_shtc3
	sht = adafruit_shtc3.SHTC3(i2c)
	temperature, relative_humidity = sht.measurements
	sh_temp = str("Temperature: %0.1f C" % temperature)
	sh_humi = str("Humidity: %0.1f %%" % relative_humidity)
	print(f"Read SHTC3: {sh_temp}, {sh_humi}")

def test_sps30():
	import sps30
	global sps
	sps = sps30.SPS30(1)
	if sps.read_article_code() == sps.ARTICLE_CODE_ERROR:
		raise Exception("SPS30: ARTICLE CODE CRC ERROR!")
	else:
		print("SPS30: ARTICLE CODE: " + str(sps.read_article_code()))

	if sps.read_device_serial() == sps.SERIAL_NUMBER_ERROR:
		raise Exception("SPS30: SERIAL NUMBER CRC ERROR!")
	else:
		print("SPS30: DEVICE SERIAL: " + str(sps.read_device_serial()))

	sps.set_auto_cleaning_interval(604800) # default 604800, set 0 to disable auto-cleaning

	sps.device_reset() # device has to be powered-down or reset to check new auto-cleaning interval
	if sps.read_auto_cleaning_interval() == sps.AUTO_CLN_INTERVAL_ERROR: # or returns the interval in seconds
		raise Exception("SPS30: AUTO-CLEANING INTERVAL CRC ERROR!")
	else:
		print("SPS30: AUTO-CLEANING INTERVAL: " + str(sps.read_auto_cleaning_interval()))

	time.sleep(5)
	sps.start_measurement()
	time.sleep(5)

	print("SPS30: Measuring")
	if not sps.read_data_ready_flag():
		if sps.read_data_ready_flag() == sps.DATA_READY_FLAG_ERROR:
			raise Exception("SPS30: DATA-READY FLAG CRC ERROR!")
	elif sps.read_measured_values() == sps.MEASURED_VALUES_ERROR:
		raise Exception("SPS30: MEASURED VALUES CRC ERROR!")
	sps30_pm1 = str("PM1.0: %0.1f µg/m3" % sps.dict_values['pm1p0'])
	sps30_pm2p5 = str("PM2.5: %0.1f µg/m3" % sps.dict_values['pm2p5'])
	sps30_pm10 = str("PM10 : %0.1f µg/m3" % sps.dict_values['pm10p0'])
	sps30_nc1 = str("NC1.0: %0.1f 1/cm3" % sps.dict_values['nc1p0'])
	sps30_nc4 = str("NC4.0: %0.1f 1/cm3" % sps.dict_values['nc4p0'])
	sps30_typ = str("Typical Particle: %0.1f µm" % sps.dict_values['typical'])
	print(f"SPS30 readouts:")
	print(sps30_pm1+" "+sps30_pm2p5+" "+sps30_pm10+" "+sps30_nc1+" "+sps30_nc4+" "+sps30_typ)

def test_t6713():
	obj_6713 = T6713()
	t6713_stt = str("T6713 status:"+str(bin(obj_6713.status())))
	t6713_ppm = str(" PPM: "+str(obj_6713.gasPPM()))
	t6713_abc = str(" ABC state: "+str(obj_6713.checkABC()))
	print(t6713_stt+t6713_ppm+t6713_abc)

# T6713 start
bus = 1
addressT6713 = 0x15
I2C_SLAVE=0x0703

class i2c_6713(object):
	def __init__(self, device, bus):

		self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
		self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

		# set device address

		fcntl.ioctl(self.fr, I2C_SLAVE, device)
		fcntl.ioctl(self.fw, I2C_SLAVE, device)

	def write(self, bytes):
		self.fw.write(bytes)

	def read(self, bytes):
		return self.fr.read(bytes)

	def close(self):
		self.fw.close()
		self.fr.close()

class T6713(object):
	def __init__(self):
		self.dev = i2c_6713(addressT6713, bus)

	def status(self):
		logging.debug('Running function:'+inspect.stack()[0][3])
		buffer = array.array('B', [0x04, 0x13, 0x8a, 0x00, 0x01])
		self.dev.write(buffer)
		time.sleep(0.1)
		data = self.dev.read(4)
		buffer = array.array('B', data)
		return buffer[2]*256+buffer[3]

	def send_cmd(self, cmd):
		buffer = array.array('B', cmd)
		self.dev.write(buffer)
		time.sleep(0.01) # Technically minimum delay is 10ms 
		data = self.dev.read(5)
		buffer = array.array('B', data)
		return buffer

	def reset(self):
		logging.debug('Running function:'+inspect.stack()[0][3])
		buffer = array.array('B', [0x04, 0x03, 0xe8, 0x00, 0x01])
		self.dev.write(buffer)
		time.sleep(0.01)
		data = self.dev.read(5)
		buffer = array.array('B', data)
		cmd_result = 1
		if ((buffer[2] == 0xe8) & (buffer[3] == 0xff) & (buffer[4] == 0x00)): cmd_result = 0 
		return buffer

	def gasPPM(self):
		logging.debug('Running function:'+inspect.stack()[0][3])
		buffer = array.array('B', [0x04, 0x13, 0x8b, 0x00, 0x01])
		self.dev.write(buffer)
		time.sleep(0.1)
		data = self.dev.read(4)
		buffer = array.array('B', data)
		ret_value = int((((buffer[2] & 0x3F) << 8) | buffer[3]))
		logging.info("Read gasPPM ("+str(ret_value)+")")
		return ret_value
		#return buffer[2]*256+buffer[3]

	def checkABC(self):
		logging.debug('Running function:'+inspect.stack()[0][3])
		buffer = array.array('B', [0x04, 0x03, 0xee, 0x00, 0x01])
		self.dev.write(buffer)
		time.sleep(0.1)
		data = self.dev.read(4)
		buffer = array.array('B', data)
		return buffer[2]*256+buffer[3]

	def calibrate(self):
		logging.debug('Running function:'+inspect.stack()[0][3])
		buffer = array.array('B', [0x05, 0x03, 0xec, 0xff, 0x00])
		self.dev.write(buffer)
		time.sleep(0.1)
		data = self.dev.read(5)
		buffer = array.array('B', data)
		return buffer[3]*256+buffer[3]

# T6713 end

def test_oled():
	import Adafruit_SSD1306
	from PIL import Image
	from PIL import ImageDraw
	from PIL import ImageFont

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

def main():
	# Warm up GPIO
	gpio_start()
	print(f"Starting {bcolors.HIGH}GPIO{bcolors.TEXT}: {bcolors.PASS}PASS{bcolors.TEXT}")
	# Start menu
	exit_sel = False
	options = ["SHTC3", "SPS30", "T6713", "OLED", "All", "Exit"]
	terminal_menu = TerminalMenu(options)
	while not (exit_sel):
		menu_entry_index = terminal_menu.show()
		exit_sel = (options[menu_entry_index] == "Exit")
		test_all = (options[menu_entry_index] == "All")
		if not (exit_sel): 
			if (test_all):
				for i in ["SHTC3", "SPS30", "T6713", "OLED"]:
					test_good = test(i)
					test_out = f"{bcolors.PASS}PASS{bcolors.TEXT}" if test_good else f"{bcolors.FAIL}FAIL{bcolors.TEXT}"
					print(f"Testing {bcolors.HIGH}{i}{bcolors.TEXT}: "+test_out)
			else:
				test_good = test(options[menu_entry_index])
				test_out = f"{bcolors.PASS}PASS{bcolors.TEXT}" if test_good else f"{bcolors.FAIL}FAIL{bcolors.TEXT}"
				print(f"Testing {bcolors.HIGH}{options[menu_entry_index]}{bcolors.TEXT}: "+test_out)

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		GPIO.cleanup()
		logging.exception("main crashed. Error: %s", e)
