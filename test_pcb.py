# This is a code aimed to test the PCB
# Requires: sudo python3 -m pip install simple-term-menu

#!/usr/bin/env python3

from simple_term_menu import TerminalMenu
import logging, os, inspect, logging.handlers
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
        print("Testing SHTC3")
        try: 
            print("Running SHTC3")
            test_shtc3()
            res_test = True
        except: res_test = False
    elif comp_test == "SPS30":
        print("Testing SPS30")
        try: 
            print("Running SPS30")
            test_sps30()
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

    print("Measuring")
    sps30_pm1 = str("PM1.0: %0.1f µg/m3" % sps.dict_values['pm1p0'])
    sps30_pm2p5 = str("PM2.5: %0.1f µg/m3" % sps.dict_values['pm2p5'])
    sps30_pm10 = str("PM10 : %0.1f µg/m3" % sps.dict_values['pm10p0'])
    sps30_nc1 = str("NC1.0: %0.1f 1/cm3" % sps.dict_values['nc1p0'])
    sps30_nc4 = str("NC4.0: %0.1f 1/cm3" % sps.dict_values['nc4p0'])
    sps30_typ = str("Typical Particle: %0.1f µm" % sps.dict_values['typical'])
    print(f"SPS30 readouts:")
    print(sps30_pm1)
    print(sps30_pm2p5)
    print(sps30_pm10)
    print(sps30_nc1)
    print(sps30_nc4)
    print(sps30_typ)

def main():
    # Warm up GPIO
    gpio_start()
    print(f"Starting {bcolors.HIGH}GPIO{bcolors.TEXT}: {bcolors.PASS}PASS{bcolors.TEXT}")
    # Start menu
    exit_sel = False
    options = ["SHTC3", "SPS30", "T6713", "OLED", "exit"]
    terminal_menu = TerminalMenu(options)
    while not (exit_sel):
        menu_entry_index = terminal_menu.show()
        exit_sel = (options[menu_entry_index] == "exit")
        if not (exit_sel): 
            test_good = test(options[menu_entry_index])
            test_out = f"{bcolors.PASS}PASS{bcolors.TEXT}" if test_good else f"{bcolors.FAIL}FAIL{bcolors.TEXT}"
            print(f"Testing {bcolors.HIGH}{options[menu_entry_index]}{bcolors.TEXT}: "+test_out)

if __name__ == "__main__":
    main()

exit(0)
#!/usr/bin/python
import math, struct, array, time, io, fcntl
import board
import adafruit_shtc3
import Adafruit_SSD1306
## SPS30
import sps30
## SPS30
import DBSETUP  # import the db setup

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# Panels
PANEL_NUM = 3
PANEL_DELAY = 30 # In seconds
cur_panel = 1

# DB
DB_SAMPLE_PERIOD = 10 # Write the samples to the DB every DB_SAMPLE_PERIOD seconds


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
temperature, relative_humidity = sht.measurements

# Connect T6713
## T6713
# obj_6713 = T6713()
## T6713

# If Reset needed - uncomment
# t6713_reset = obj.reset()
# print("T6713 reset returned:")
# print(','.join(format(x, '02x') for x in t6713_reset))

# Prep the air quality sensor
## SPS30
sps = sps30.SPS30(1)
try:
	if sps.read_article_code() == sps.ARTICLE_CODE_ERROR:
		raise Exception("ARTICLE CODE CRC ERROR!")
	else:
		print("ARTICLE CODE: " + str(sps.read_article_code()))

	if sps.read_device_serial() == sps.SERIAL_NUMBER_ERROR:
		raise Exception("SERIAL NUMBER CRC ERROR!")
	else:
		print("DEVICE SERIAL: " + str(sps.read_device_serial()))

	sps.set_auto_cleaning_interval(604800) # default 604800, set 0 to disable auto-cleaning

	sps.device_reset() # device has to be powered-down or reset to check new auto-cleaning interval

	if sps.read_auto_cleaning_interval() == sps.AUTO_CLN_INTERVAL_ERROR: # or returns the interval in seconds
		raise Exception("AUTO-CLEANING INTERVAL CRC ERROR!")
	else:
		print("AUTO-CLEANING INTERVAL: " + str(sps.read_auto_cleaning_interval()))

	sps.start_measurement()

except Exception as e:
	green_led.set_led(0)
	GPIO.cleanup()
	logging.exception("main crashed during SPS30 readout. Error: %s", e)
## SPS30

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
			# draw.text((x, top+8*5), "T6713 (Status:"+str(bin(obj_6713.status())+")"),  font=font, fill=255)
			# draw.text((x, top+8*6), str("PPM: "+str(obj_6713.gasPPM())),  font=font, fill=255)
			# draw.text((x, top+8*7), str("ABC State: "+str(obj_6713.checkABC())),  font=font, fill=255)
## T6713
		if (panel_id == 2):
			draw.text((x, top+8*1), "SENSORS: Air Quality",  font=font, fill=255)
## SPS30
			draw.text((x, top+8*2), str("PM1.0: %0.1f µg/m3" % sps.dict_values['pm1p0']),  font=font, fill=255)
			draw.text((x, top+8*3), str("PM2.5: %0.1f µg/m3" % sps.dict_values['pm2p5']),  font=font, fill=255)
			draw.text((x, top+8*4), str("PM10 : %0.1f µg/m3" % sps.dict_values['pm10p0']),  font=font, fill=255)
			draw.text((x, top+8*5), str("NC1.0: %0.1f 1/cm3" % sps.dict_values['nc1p0']),  font=font, fill=255)
			draw.text((x, top+8*6), str("NC4.0: %0.1f 1/cm3" % sps.dict_values['nc4p0']),  font=font, fill=255)
			draw.text((x, top+8*7), str("Typical Particle: %0.1f µm" % sps.dict_values['typical']),  font=font, fill=255)
## SPS30
	except Exception as e:
		green_led.set_led(0)
		GPIO.cleanup()
		logging.exception("main crashed during panel display. Error: %s", e)

#		print ("PM4.0 Value in µg/m3: " + str(sps.dict_values['pm4p0']))
#		print ("NC0.5 Value in 1/cm3: " + str(sps.dict_values['nc0p5']))    # NC: Number of Concentration 
#		print ("NC2.5 Value in 1/cm3: " + str(sps.dict_values['nc2p5']))
#		print ("NC10.0 Value in 1/cm3: " + str(sps.dict_values['nc10p0']))

def saveResults():
	DBSETUP.ganacheLogger(float(temperature), "Temperature", "C", "MAC_T", "unit_descrip", "SHTC3", "Sensirion")	
	DBSETUP.ganacheLogger(float(relative_humidity), "Humidity", "%", "MAC_H", "unit_descrip", "SHTC3", "Sensirion")
## T6713
	# DBSETUP.ganacheLogger(float(obj_6713.gasPPM()), "CO2 Concentration", "PPM", "MAC_CO2", "unit_descrip", "T6713", "Amphenol Advanced Sensors")
	# DBSETUP.ganacheLogger(float(obj_6713.checkABC()), "CO2 ABC State", " ", "MAC_CO2_ABC", "unit_descrip", "T6713", "Amphenol Advanced Sensors")
## T6713
## SPS30
	DBSETUP.ganacheLogger(float(sps.dict_values['pm1p0']), "AQ_PM1.0", "µg/m3", "MAC_AQ_1", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['pm2p5']), "AQ_PM2.5", "µg/m3", "MAC_AQ_2", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['pm4p0']), "AQ_PM4", "µg/m3", "MAC_AQ_3", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['pm10p0']), "AQ_PM10", "µg/m3", "MAC_AQ_4", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['nc0p5']), "AQ_NC0_5", "1/cm3", "MAC_AQ_5", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['nc1p0']), "AQ_NC1", "1/cm3", "MAC_AQ_6", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['nc2p5']), "AQ_NC2_5", "1/cm3", "MAC_AQ_7", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['nc4p0']), "AQ_NC4", "1/cm3", "MAC_AQ_8", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['nc10p0']), "AQ_NC10", "1/cm3", "MAC_AQ_9", "unit_descrip", "SPS30", "Sensirion")
	DBSETUP.ganacheLogger(float(sps.dict_values['typical']), "AQ_NC0_TYPICAL", "µm", "MAC_AQ_10", "unit_descrip", "SPS30", "Sensirion")
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
		try: 
			if not sps.read_data_ready_flag():
				if sps.read_data_ready_flag() == sps.DATA_READY_FLAG_ERROR:
					raise Exception("DATA-READY FLAG CRC ERROR!")
			elif sps.read_measured_values() == sps.MEASURED_VALUES_ERROR:
				raise Exception("MEASURED VALUES CRC ERROR!")
		except Exception as e:
			raise Exception("SPS30: read_data_ready_flag raised exception: %s", e)		
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
