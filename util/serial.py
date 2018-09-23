#!/usr/bin/env python3

import time, serial, json

class Serial:

    def __init__(self, config):
        self.serial_config = config.get_serial_config()
        self.interfaces = self.serial_config["interfaces"]
        self.prev_values = [0] * len( self.interfaces )
        self.initialized = False

        self.conn = serial.Serial( self.serial_config["path"], baudrate=self.serial_config["baudrate"] )

    def read_serial(self):
        self.conn.write(bytearray('t','ascii')) # trigger arduino to report total data
        while (self.conn.inWaiting() == 0):
            time.sleep(0.001)
        data = self.conn.readline().decode("utf-8")
        return json.loads(data) # parse string result as json

    def get_power_since_last_request(self):
        diff = [0] * len(self.interfaces)
        if self.initialized:
            new_values = self.read_serial()[0:len( self.interfaces )]
            diff = [i - j for i, j in zip(new_values, self.prev_values)]
        else: self.initialized = True
        self.prev_values = new_values
        return diff


    def close(self):
        self.conn.close()

if __name__ == '__main__':

    print('nothing to do here')
