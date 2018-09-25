# s0-bridge

Include your power consumption as well as non Bluetooth(R) or Speedwire enabled solar inverters into your SBFspot database by using power meters with S0 interface.

This project uses a Raspberry Pi running SBFspot which carries an Arduino Pro Mini 3.3V piggyback to collect S0 pulses from power meters.

**NOTE**: The used circuit provides a voltage of 5VDC to the S0 interface of a connected power meter. This may not be sufficient for every S0 interface. The circuit diagram can certainly be adjusted accordingly the specs of any S0-enabled power meter, but I will not provide any support therefore. However, it works well with the _Eltako DSZ15D_ for example.


## Software

### Install dependencies

```bash
sudo apt install python3 python3-pip
sudo pip3 install pyserial pytz
```

### Enable Pis serial interface
 
 1. Enter `sudo raspi-config`
 1. Choose _1 Interfacing Options_
 1. Choose _P6 Serial_
 1. Disable shell via serial interface
 1. Enable serial port hardware
 1. Reboot the Pi

### Start the bridge

```python
python3 s0-bridge.py
```

To run _s0-bridge_ on boot:
```bash
# make the scripts executable
sudo chmod 755 s0-bridge.py
sudo chmod 755 s0-bridge.sh

# add the bash script to the service folder
sudo cp s0-bridge.sh /etc/init.d/s0-bridge
sudo update-rc.d s0-bridge defaults
```

## Hardware and wiring

Parts needed:

* Raspberry Pi 3
* Arduino Pro Mini 3.3V (Clone)
* 2k2Ω and 3k3Ω resistors
* Breadboard and wires

<img src="arduino/s0-bridge_breadboard.png?raw=true" alt="Arduino Pro Mini 3.3V breadboard"  width="500">

## Disclaimer 

**Dealing with mains voltage is life-threatening!** 

The project uses only low voltage, but usually the power distribution box needs to be opened for connecting cables to the S0 interface. I expressly point out that this, as well as the installation of an electricity meter, may only be performed by qualified personnel.

