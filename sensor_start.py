#!/usr/bin/python
import math, struct, array, time, io, fcntl
import logging, os, inspect, logging.handlers
import board
import adafruit_shtc3
import Adafruit_SSD1306
import sps30
import DBSETUP  # import the db setup

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

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
PANEL_DELAY = 10 # In seconds

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
	logging.exception("Main crashed. Error: %s", e)
	  
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
obj_6713 = T6713()
# If Reset needed - uncomment
# t6713_reset = obj.reset()
# print("T6713 reset returned:")
# print(','.join(format(x, '02x') for x in t6713_reset))

# Prep the air quality sensor
sps = sps30.SPS30(1)
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

# Configure the display panel
def showPanel(panel_id):
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
        draw.text((x, top+8*5), "T6713 (Status:"+str(bin(obj_6713.status())+")"),  font=font, fill=255)
        draw.text((x, top+8*6), str("PPM: "+str(obj_6713.gasPPM())),  font=font, fill=255)
        draw.text((x, top+8*7), str("ABC State: "+str(obj_6713.checkABC())),  font=font, fill=255)
    if (panel_id == 2):
        draw.text((x, top+8*1), "SENSORS: Air Quality",  font=font, fill=255)
        draw.text((x, top+8*2), str("PM1.0: %0.1f µg/m3" % sps.dict_values['pm1p0']),  font=font, fill=255)
        draw.text((x, top+8*3), str("PM2.5: %0.1f µg/m3" % sps.dict_values['pm2p5']),  font=font, fill=255)
        draw.text((x, top+8*4), str("PM10 : %0.1f µg/m3" % sps.dict_values['pm10p0']),  font=font, fill=255)
        draw.text((x, top+8*5), str("NC1.0: %0.1f 1/cm3" % sps.dict_values['nc1p0']),  font=font, fill=255)
        draw.text((x, top+8*6), str("NC4.0: %0.1f 1/cm3" % sps.dict_values['nc4p0']),  font=font, fill=255)
        draw.text((x, top+8*7), str("Typical Particle: %0.1f µm" % sps.dict_values['typical']),  font=font, fill=255)

#		print ("PM4.0 Value in µg/m3: " + str(sps.dict_values['pm4p0']))
#		print ("NC0.5 Value in 1/cm3: " + str(sps.dict_values['nc0p5']))    # NC: Number of Concentration 
#		print ("NC2.5 Value in 1/cm3: " + str(sps.dict_values['nc2p5']))
#		print ("NC10.0 Value in 1/cm3: " + str(sps.dict_values['nc10p0']))

def saveResults():
	DBSETUP.ganacheLogger(float(temperature), "Temperature", "C", "MAC_T", "unit_descrip", "SHTC3", "Sensirion")	
	DBSETUP.ganacheLogger(float(relative_humidity), "Relative Humidity", "%", "MAC_H", "unit_descrip", "SHTC3", "Sensirion")
	DBSETUP.ganacheLogger(float(obj_6713.gasPPM()), "CO2 Concentration", "PPM", "MAC_CO2", "unit_descrip", "T6713", "Amphenol Advanced Sensors")
	DBSETUP.ganacheLogger(float(obj_6713.checkABC()), "CO2 ABC State", " ", "MAC_CO2_ABC", "unit_descrip", "T6713", "Amphenol Advanced Sensors")
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
	global IP, CPU, MemUsage, Disk, temperature, relative_humidity, obj_6713, sps
	cur_panel = 1
	panel_start = time.time()
	str_panel_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(panel_start))
	print(str_panel_start+": main started")
	while True:
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
		logging.debug('Reading SPS30 data')
		try: 
			if not sps.read_data_ready_flag():
				if sps.read_data_ready_flag() == sps.DATA_READY_FLAG_ERROR:
					raise Exception("DATA-READY FLAG CRC ERROR!")
			elif sps.read_measured_values() == sps.MEASURED_VALUES_ERROR:
				raise Exception("MEASURED VALUES CRC ERROR!")
		except Exception as e:
			raise Exception("SPS30: read_data_ready_flag raised exception: %s", e)		

		# Set display
		if (time.time()-panel_start > PANEL_DELAY):
			cur_panel = (cur_panel+1) % PANEL_NUM
			panel_start = time.time()
		showPanel(cur_panel)

		# Display image.
		disp.image(image)
		disp.display()
		time.sleep(1)

if __name__ == "__main__":
   try:
      main()
   except Exception as e:
      logging.exception("main crashed. Error: %s", e)