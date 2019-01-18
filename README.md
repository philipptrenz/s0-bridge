# s0-bridge

Include your power consumption as well as non Bluetooth(R) or Speedwire enabled solar inverters into a SBFspot database by using power meters with S0 interface.

Modern solar power inverters from the manufacturer SMA are equipped with ethernet or Bluetooth(R) interfaces. Therefore [SBFspot](https://github.com/SBFspot/SBFspot) provides a nice way to collect parameters and energy production of these devices. This project provides a way to collect production data of non-ethernet or Bluetooth(R) enabled inverters, also from different manufacturers, as well as energy consumption. This data is collected by using electricity meters with S0 interfaces, which are read by microcontrollers. These communicate with a Raspberry Pi via serial interface (cable) or WiFi, the Raspberry Pi stores the data in the database of SBFspot.

The following parts are needed:

* Raspberry Pi (3)
* Arduino Pro Mini 3.3V (Clone) OR ESP8266 NodeMCU (LoLin)
* USB-to-TTL adapter (only for Arduino Pro Mini)
* Breadboard and jumper wires
* 2k2Ω and 3k3Ω resistors for voltage division (5V to 3.3V)
* optional: skrew terminals, housing etc.

If you like my project and want to keep me motivated:

<a href='https://ko-fi.com/U7U6COXD' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi2.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

Also check out my [sunportal](https://github.com/philipptrenz/sunportal) project providing a web based visualisation of SBFspot data!

## Software for the Microcontroller

Just flash `arduino/sketch_s0_serial.ino` to the Pro Mini or if you want to use the ESP8266 NodeMCU use `arduino/sketch_s0_wifi.ino`. Both Microcontrollers get flashed by using the Arduino IDE, there are many tutorials out there showing how.

**NOTE:** It's important to have the 3.3V version of the Arduino Pro Mini to communicate directly to the Raspberry Pis UART interface. If you insist to use a 5V Arduino this can be done using a voltage level shifter.


## Software for the Raspberry Pi

### Enable Pis serial interface
 
 1. Enter `sudo raspi-config`
 1. Choose _1 Interfacing Options_
 1. Choose _P6 Serial_
 1. Disable shell via serial interface
 1. Enable serial port hardware
 1. Reboot the Pi

### Install dependencies

```bash
sudo apt install python3 python3-pip
sudo pip3 install -r requirements.txt
``` 

### Configure _s0-bridge_

The project includes the following config file in json format:

```json
{
	"database": {
		"path": "/home/pi/smadata/SBFspot.db"
	},
	"data_interfaces": {
		"serial": {
			"path": "/dev/serial0",
			"baudrate": 115200,
			"timeout": 1,
			"interfaces": [
				{
					"serial_id": "1000000001",
					"name": "My Power Plant",
					"type": "inverter",
					"prev_etotal": 0,
					"pulses_per_kwh": 1000
				}
			]
		},
		"network": {
			"interfaces": []
		}
	}
}
```

To edit it to your needs copy the file to `config.json`:

```bash
cp config.default.json config.json
```

Under `data_interfaces.serial.interfaces` has to be a json object for each s0 interface in the same order as connected to the Pro Mini. Available types are `inverter` and `consumption`, `serial_id` and `name` can be chosen freely. With `prev_etotal` the previous power production or consumption can be added in Wh and `pulses_per_kwh` has to be set accordingly the specs of the connected power meter.

### Start _s0-bridge_

```python
python3 s0-bridge.py
```

### Run _s0-bridge_ on boot

```bash
# make the scripts executable
sudo chmod 755 s0-bridge.*

# add the bash script to the service folder
sudo cp s0-bridge.sh /etc/init.d/s0-bridge
sudo update-rc.d s0-bridge defaults
``` 

## Hardware and wiring

### Arduino Pro Mini

Wire the Arduino Pro Mini to the Raspberry Pi as shown below:

<img src="arduino/s0-bridge_breadboard.png?raw=true" alt="Arduino Pro Mini 3.3V breadboard"  width="500">

The Arduino Sketch supports up to three S0 inputs (on pins 2, 3 and 4), but can easily be extended.

**NOTE**: The circuit provides a voltage of 5VDC to the S0 interface of a connected power meter. This may not be sufficient for every S0 interface. The circuit diagram can certainly be adjusted accordingly the specs of any S0-enabled power meter, but I will not provide any support therefore. However, it works well with the _Eltako DSZ15D_ for example.

### NodeMCU (ESP8266)

(coming soon)

## Disclaimer 

**Dealing with mains voltage is life-threatening!** 

The project uses only low voltage, but usually the power distribution box needs to be opened for connecting cables to the S0 interface. I expressly point out that this, as well as the installation of an electricity meter, may only be performed by qualified personnel.

SMA, Speedwire are registered trademarks of SMA Solar Technology AG.
