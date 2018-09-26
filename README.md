# s0-bridge

Include your power consumption as well as non Bluetooth(R) or Speedwire enabled solar inverters into your SBFspot database by using power meters with S0 interface.

This project uses a Raspberry Pi running SBFspot which carries an Arduino Pro Mini 3.3V piggyback to collect S0 pulses from power meters.

The following parts are needed:

* Raspberry Pi (3)
* Arduino Pro Mini 3.3V (Clone)
* USB-to-TTL adapter supporting 3.3V and having a DTR pin 
* Breadboard and jumper wires
* 2k2Ω and 3k3Ω resistors for voltage division (5V to 3.3V)
* optional: skrew terminals

Also check out my [sunportal](https://github.com/philipptrenz/sunportal) project providing a web based visualisation of SBFspot data!

## Flashing the Arduino Pro Mini

Just flash `arduino/sketch_s0_serial.ino` to the Pro Mini using the Arduino IDE and a USB-to-TTL adapter.

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
sudo pip3 install pyserial pytz
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
sudo chmod 755 s0-bridge.py
sudo chmod 755 s0-bridge.sh

# add the bash script to the service folder
sudo cp s0-bridge.sh /etc/init.d/s0-bridge
sudo update-rc.d s0-bridge defaults
``` 

## Hardware and wiring

Wire the Arduino Pro Mini to the Raspberry Pi as shown below:

<img src="arduino/s0-bridge_breadboard.png?raw=true" alt="Arduino Pro Mini 3.3V breadboard"  width="500">

The Arduino Sketch supports up to three S0 inputs (on pins 2, 3 and 4), but can easily be extended.

**NOTE**: The circuit provides a voltage of 5VDC to the S0 interface of a connected power meter. This may not be sufficient for every S0 interface. The circuit diagram can certainly be adjusted accordingly the specs of any S0-enabled power meter, but I will not provide any support therefore. However, it works well with the _Eltako DSZ15D_ for example.

## Disclaimer 

**Dealing with mains voltage is life-threatening!** 

The project uses only low voltage, but usually the power distribution box needs to be opened for connecting cables to the S0 interface. I expressly point out that this, as well as the installation of an electricity meter, may only be performed by qualified personnel.

