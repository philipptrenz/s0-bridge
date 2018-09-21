#!/usr/bin/env python3

import time, serial, json

class Serial:

    def __init__(self, config):
        self.config = config
        self.interfaces = self.config.get_serial_interfaces()
        self.prev_values = [0] * len( self.interfaces )

        self.conn = serial.Serial( '/dev/serial0', baudrate=115200 )

    def read_serial(self):
        self.conn.write(bytearray('t','ascii')) # trigger arduino to report total data
        while (self.conn.inWaiting() == 0):
            time.sleep(0.001)
        data = self.conn.readline().decode("utf-8")
        return json.loads(data)

    def get_power_since_last_request(self):
        new_values = self.read_serial()[0:len( self.interfaces )]
        diff = [i - j for i, j in zip(new_values, self.prev_values)]
        self.prev_values = new_values
        return diff


    def close(self):
        self.conn.close()

if __name__ == '__main__':

    print('nothing to do here')
