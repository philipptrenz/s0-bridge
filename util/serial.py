#!/usr/bin/env python3

import time, serial, json

class Serial:

    def __init__(self, config):
        self.cfg = config
        self.serial_config = config.get_serial_config()
        self.interfaces = self.serial_config["interfaces"]
        self.timeout = self.serial_config["timeout"]
        self.is_enabled = self.serial_config["enabled"]

        self.prev_values = [0] * len( self.interfaces )
        self.last_retrieved = 0

        self.unsigned_long_max_size = 2**32-1

        self.conn = serial.Serial(
            port=self.serial_config["path"],
            baudrate=self.serial_config["baudrate"],
            timeout=self.serial_config["timeout"]
        )

        if self.is_enabled:
            self.get_power_since_last_request(True)

    def read_serial(self):
        self.conn.write(bytearray('t','ascii')) # trigger arduino to report total data
        while (self.conn.inWaiting() == 0):
           time.sleep(0.001)
        raw_data = self.conn.readline()
        data = raw_data.decode("utf-8")

        if data == '' or data == 't':
            raise Exception('serial: no data received, serial timeout')

        json_obj = json.loads(data)
        return json_obj # parse string result as json

    def get_power_since_last_request(self, initial_request=False):
        diff = [0] * len(self.interfaces)
        new_values = []

        if not initial_request: self.cfg.log('serial: collecting data from serial interface')

        try:
            new_values = self.read_serial()[0:len(self.interfaces)]
        except Exception as e:

            if not initial_request: self.cfg.log(e)
            new_values = [0] * len( self.interfaces )

        now = time.time()
        if not self.last_retrieved == 0:
            for idx in range(len(self.interfaces)):
                diff[idx] = new_values[idx] - self.prev_values[idx]
                if new_values[idx] < self.prev_values[idx]: # arduino unsigned long overflow
                    diff[idx] = self.unsigned_long_max_size - self.prev_values[idx] + new_values[idx]



            diff = [i - j for i, j in zip(new_values, self.prev_values)] # Pulses since last retrieval
        self.prev_values = new_values

        res = []
        for idx, source in enumerate(self.interfaces):

            power = 0
            watts = 0
            if self.last_retrieved != 0:
                pulses = diff[idx]
                watts = int(pulses / source["pulses_per_kwh"] * 1000)      # convert pulses to Wh
                power = int(watts / (now - self.last_retrieved) * 3600) # calculate avg power production in Wh

            res.append({
                "energy": watts,
                "power": power,
                "source": source
            })

        self.last_retrieved = now
        return res


    def close(self):
        self.conn.close()

if __name__ == '__main__':

    print('nothing to do here')
