# Blockpenn-python
Python code for the RPi sensors.

See our [Documentation Website](https://liogl.github.io/blockpenn-python/#/).

## Installation
Tested with Ubuntu 22.04 LTS Server 64 bit. 
1. Complete deploying the docker image of blockpenn on the RPi. 
2. Set up the environment.
3. (Optional) Use `test_pcb.py` to test the different components on the PCB. This will let you know if there are any issues with a specific component (e.g. sensor, OLED).
4. Run `sensor_start_w_sps_v2.py` manually to test the setup.
5. Set up crontab to auto start the script in reboot.

### sensor_start_w_sps_v2
This is the Python code with all sensors (Air quality, CO2, Humidity & Temp) and OLED display.
This code is designed for the V2 of the SensorBoard. 

### Environment setup
This part covers how to set up the environment. 

#### Setting up the environment (Manual)
This is only needed if you didn't run the script to set up the environment.
General:
```sh
sudo python3 -m venv .
source ./bin/activate
sudo apt install python3-pip
sudo pip3 install influxdb
sudo python3 -m pip install simple-term-menu
sudo apt install python3-lgpio
sudo apt-get install libgpiod2
sudo apt install -y python3-rpi.gpio
sudo apt install -y python3-pil
git clone https://github.com/adafruit/Adafruit_Python_SSD1306.git
cd Adafruit_Python_SSD1306
sudo pip3 install Adafruit_SSD1306
sudo python3 setup.py install
cd ..
sudo pip3 install adafruit-circuitpython-shtc3 sps30 smbus2
```

#### Setting up the environment (Script) 
**Note: currently not working**

There are two ways to set up the environment: 
1. Using a script (recommended)
2. Manually

```sh
sudo sh setup_pkg.sh
sh setup_env.sh
```
Then run:
```sh
cd Adafruit_Python_SSD1306
sudo pip3 install Adafruit_SSD1306
sudo python3 setup.py install
cd ..
sudo pip3 install adafruit-circuitpython-shtc3
sudo pip3 install smbus2
sudo pip3 install influxdb
```

### Set up crontab to auto start the script in reboot
Open crontab:
```sh
sudo crontab -e
```
Pick your preferred editor and add the following line to the crontab file:
```
@reboot sh /home/ubuntu/blockpenn-python/run_sensor_script.sh >> /var/log/sensor_script.log 2>&1
```

Test by rebooting.

## To test the PCB

Run the following command: `sudo python3 test_pcb.py`

## Links
- Useful I2C commands: https://www.waveshare.com/wiki/Raspberry_Pi_Tutorial_Series:_I2C
- T6713 datasheet: http://www.co2meters.com/Documentation/Datasheets/DS-AMP-0002-T6713-Sensor.pdf
- T6713 application notes: https://f.hubspotusercontent40.net/hubfs/9035299/Documents/AAS-916-142A-Telaire-T67xx-CO2-Sensor-022719-web.pdf
- T6713 digikey page: https://www.digikey.com/en/products/detail/amphenol-advanced-sensors/T6713/5027891
- I2C UM10204: https://www.nxp.com/docs/en/user-guide/UM10204.pdf
- Connectd guide to reading SHTC3: https://blog.dbrgn.ch/2018/8/20/read-shtc3-sensor-from-linux-raspberry-pi/
- Python Kasa: https://python-kasa.readthedocs.io/en/latest/smartplug.html
- SPS30 datasheet: https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.6_Particulate_Matter/Datasheets/Sensirion_PM_Sensors_Datasheet_SPS30.pdf
- SPS30 page: https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/
- Good diagram of particles types (p. 13): https://cdn-learn.adafruit.com/downloads/pdf/pm25-air-quality-sensor.pdf

## Documentation Website
Our [awesome documentation website](https://liogl.github.io/BlockPenn-Python) was created using [docsify](https://docsify.js.org/#/)

## To "refresh" an RPi

```sh
sudo apt update
sudo apt upgrade
```