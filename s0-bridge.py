#!/usr/bin/env python3
import time as t, math
from datetime import datetime, date, time, timedelta

from util.config import Config
from util.database import Database
from util.serial  import Serial

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100

def collect_data(db, ts):
    ts_log = roundup(ts)

    # serial data
    new_serial_data = ser.get_power_since_last_request()
    db.add_data(ts_log, new_serial_data)

    #print(ts_log, '\t', 'watts:', new_serial_data[0]['watts'], ', power:', new_serial_data[0]['power'], '\t', datetime.now())



if __name__ == '__main__':

    config = Config()
    db = Database(config)
    ser = Serial(config)

    print('S0 SBFspot bridge started \n')

    # initialize
    db.add_inverters()

    try:

        while True:
            ts =  datetime.now().timestamp()
            # before minute of time is a multiple of 5 minutes
            if (int(ts) % 300) == 299:
                collect_data(db, ts)
            t.sleep(1)

    except KeyboardInterrupt:
        print('Shutting down')
    except Exception as e:
        print('Error occured', e)
    finally:
        db.close()
        ser.close()