#!/usr/bin/env python3
import time as t, math, sys
from datetime import datetime
import traceback

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
            print(traceback.format_exc())
        finally:
            self.db.close()
            self.ser.close()
            sys.exit(1)


    def dry_run(self, cycles=1):

        self.cfg.log('starting dry run with 5 seconds sleep after each run')

        # initialize
        self.cfg.log('adding inverters')
        self.db.add_inverters()

        self.cfg.log('doing ' + str(cycles) + ' dry runs:')
        try:
            for _ in range(cycles):
                ts = datetime.now().timestamp()
                self.cfg.log('collecting new data')
                self.collect_data(self.db, ts, dry=True)
                t.sleep(5)
        except KeyboardInterrupt:
            print('Shutting down')
        except Exception as e:
            print('Error occured', e)
        finally:
            self.db.close()
            self.ser.close()
            sys.exit(1)


    def collect_data(self, db, ts, dry=False):
        ts_log = self.roundup(ts)

        # serial data
        if self.ser.is_enabled:
            new_serial_data = self.ser.get_power_since_last_request()
            if len(new_serial_data) > 0:
                if dry: self.cfg.log("serial data:", new_serial_data)
                if not dry: 
                    db.add_data(ts_log, new_serial_data)
                    self.cfg.log('added pv data from serial interface')

        if self.ntwrk.is_enabled:
            new_network_data = self.ntwrk.get_power_since_last_request()
            if dry: self.cfg.log("network data:", new_network_data)
            if len(new_network_data) > 0:
                if not dry: 
                    db.add_data(ts_log, new_network_data)
                    self.cfg.log('added pv data from network interfaces')

            grid_in, grid_out = self.ntwrk.get_absolute_grid_meter_data(cfg=self.cfg)
            if not dry:
                self.db.add_grid_meter_data_row(ts_log, grid_in, grid_out)
                self.cfg.log('added grid meter data from network interfaces')
            else:
                self.cfg.log('grid meter data: in = {} Wh, out = {} Wh'.format(grid_in, grid_out))


    def roundup(self, x):
        return int(math.ceil(x / 100.0)) * 100


if __name__ == '__main__':

    bridge = S0_Bridge()

    if len(sys.argv) > 1 and sys.argv[1] == 'dry':

        bridge.dry_run(cycles=3)

    else:

        bridge.start()
