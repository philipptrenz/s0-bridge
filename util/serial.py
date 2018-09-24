#!/usr/bin/env python3

import time, serial, json, random

class Serial:

    def __init__(self, config):
        self.serial_config = config.get_serial_config()
        self.interfaces = self.serial_config["interfaces"]
        self.timeout = self.serial_config["timeout"]
        self.prev_values = [0] * len( self.interfaces )
        self.last_retrieved = 0

        self.conn = serial.Serial(
            port=self.serial_config["path"],
            baudrate=self.serial_config["baudrate"],
            timeout=self.serial_config["timeout"]
        )

    def read_serial(self):
        try:
            self.conn.write(bytearray('t','ascii')) # trigger arduino to report total data
            while (self.conn.inWaiting() == 0):
               time.sleep(0.001)
            data = self.conn.readline().decode("utf-8")
            return json.loads(data) # parse string result as json
        except Exception as e:
            print('Serial: timeout exception,',e)
            return [0] * len( self.interfaces )

    def get_power_since_last_request(self):
        diff = [0] * len(self.interfaces)
        new_values = self.read_serial()[0:len(self.interfaces)]
        now = time.time()
        if not self.last_retrieved == 0:
            diff = [i - j for i, j in zip(new_values, self.prev_values)] # Pulses since last retrieval
        self.prev_values = new_values

        res = []
        for idx, inv in enumerate(self.interfaces):

            power = 0
            watts = 0
            if self.last_retrieved != 0:
                pulses = diff[idx]
                watts = int(pulses / inv["pulses_per_kwh"] * 1000)      # convert pulses to Wh
                power = int(watts / (now - self.last_retrieved) * 3600) # calculate avg power production in Wh

            res.append({
                "watts": watts,
                "power": power,
                "inverter": inv
            })

        self.last_retrieved = now
        return res


    def close(self):
        self.conn.close()

if __name__ == '__main__':

    print('nothing to do here')
