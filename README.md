# SBFspot S0 bridge

Include your power consumption as well as not Bluetooth(R) or Speedwire enabled solar inverters into your SBFspot database by using power meters with S0 interface.

This project uses a Raspberry Pi running SBFspot which carries an Arduino Pro Mini 3.3V piggyback to collect S0 pulses from power meters.

**NOTE**: This circuit only provides a voltage of 5VDC to the S0 interface of a connected power meter. This may not be sufficient for every power meters S0 interface. The circuit diagram can certainly be adjusted accordingly, but I will not provide any support on that. However, it works well with the _Eltako DSZ15D_ for example.


# Disclaimer 

Dealing with mains voltage is life-threatening! The project uses only low voltage, but usually the power distribution box needs to be opened for connecting cables to the S0 interface. I expressly point out that this, as well as the installation of an electricity meter, may only be performed by qualified personnel.