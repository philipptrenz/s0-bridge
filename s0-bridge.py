#!/usr/bin/env python3
import time as t, math, sys
from datetime import datetime

from util.config import Config
from util.database import Database
from util.serial  import Serial
from util.network import Network


class S0_Bridge:

    def __init__(self):

        print('###########################\n#    S0 SBFspot bridge    #\n###########################')

        self.cfg = Config()
        self.db = Database(self.cfg)
        self.ser = Serial(self.cfg)
        self.ntwrk = Network(self.cfg)

    def start(self):

        self.cfg.log('started')

        # initialize
        self.cfg.log('adding inverters')
        self.db.add_inverters()

        self.cfg.log('starting timed data collection (every 5 minutes)')
        try:
            while True:
                ts = datetime.now().timestamp()
                # before minute of time is a multiple of 5 minutes
                if (int(ts) % 300) == 299:
                    self.cfg.log('collecting new data')
                    self.collect_data(self.db, ts)
                t.sleep(1)

        except KeyboardInterrupt:
            print('Shutting down')
        except Exception as e:
            print('Error occured', e)
        finally:
            self.db.close()
            self.ser.close()
            sys.exit(1)


    def collect_data(self, db, ts):
        ts_log = self.roundup(ts)

        # serial data
        if self.ser.is_enabled:
            new_serial_data = self.ser.get_power_since_last_request()
            db.add_data(ts_log, new_serial_data)
            self.cfg.log('added new data from serial interface')

        if self.ntwrk.is_enabled:
            new_network_data = self.ntwrk.get_power_since_last_request()
            db.add_data(ts_log, new_network_data)

            self.ntwrk.process_consumption(db=db)
            self.cfg.log('added new data from network interfaces')

        # print(ts_log, '\t', 'watts:', new_serial_data[0]['watts'], ', power:', new_serial_data[0]['power'], '\t', datetime.now())


    def roundup(self, x):
        return int(math.ceil(x / 100.0)) * 100


if __name__ == '__main__':

    bridge = S0_Bridge()
    bridge.start()
