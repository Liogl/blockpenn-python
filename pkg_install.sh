#!/bin/bash
#Change Working Directory
cd ..

# Update and upgrade the system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y net-tools i2c-tools python3-pip python3.10-venv python3-lgpio libgpiod2 python3-rpi.gpio python3-pil

# Set up a virtual environment
python3 -m venv bpenv

# Activate the virtual environment
source bpenv/bin/activate

# Install python packages
pip3 install simple-term-menu adafruit-circuitpython-shtc3 sps30 smbus2 awsiotsdk awscrt RPi.GPIO Pillow Adafruit_SSD1306 requests python-dotenv
# Deactivate the virtual environment when done
deactivate

echo "Installation complete!"
