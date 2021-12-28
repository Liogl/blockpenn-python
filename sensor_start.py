#!/usr/bin/python
import time
import board
import adafruit_shtc3
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
# Initialize library.
disp.begin()

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

i2c = board.I2C()  # uses board.SCL and board.SDA
sht = adafruit_shtc3.SHTC3(i2c)

PANEL_NUM = 2

# Configure the display panel
def showPanel(panel_id):
    if (panel_id == 0):
        draw.text((x, top+8*1), "SYSTEM STATS",  font=font, fill=255)
        draw.text((x, top+8*2), "IP: " + str(IP.decode('utf-8')),  font=font, fill=255)
        draw.text((x, top+8*3), str(CPU.decode('utf-8')), font=font, fill=255)
        draw.text((x, top+8*4), str(MemUsage.decode('utf-8')),  font=font, fill=255)
        draw.text((x, top+8*5), str(Disk.decode('utf-8')),  font=font, fill=255)
    if (panel_id == 1):
        draw.text((x, top+8*1), "SENSORS",  font=font, fill=255)
        draw.text((x, top+8*2), "SHTC3",  font=font, fill=255)
        draw.text((x, top+8*3), str("Temperature: %0.1f C" % temperature),  font=font, fill=255)
        draw.text((x, top+8*4), str("Humidity: %0.1f %%" % relative_humidity),  font=font, fill=255)
        draw.text((x, top+8*5), "T6713",  font=font, fill=255)
        draw.text((x, top+8*6), "?????",  font=font, fill=255)

        # draw.text((x, top),       "IP: " + str(IP.decode('utf-8')),  font=font, fill=255)
        # draw.text((x, top+8*1),    str(CPU.decode('utf-8')), font=font, fill=255)
        # draw.text((x, top+8*2),    str(MemUsage.decode('utf-8')),  font=font, fill=255)
        # draw.text((x, top+8*3),    str(Disk.decode('utf-8')),  font=font, fill=255)
        # draw.text((x, top+8*4),    str("Temperature: %0.1f C" % temperature),  font=font, fill=255)
        # draw.text((x, top+8*5),    str("Humidity: %0.1f %%" % relative_humidity),  font=font, fill=255)

cur_panel = 1
PANEL_DELAY = 5 # In seconds
panel_start = time.time()

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
    if (time.time()-panel_start > PANEL_DELAY):
        cur_panel = (cur_panel+1) % PANEL_NUM
        panel_start = time.time()
    showPanel(cur_panel)

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(.1)
