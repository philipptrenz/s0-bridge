#!/usr/bin/env python3
import time as t, math
from datetime import datetime, date, time, timedelta

from util.config import Config
from util.database import Database
from util.serial  import Serial

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100


if __name__ == '__main__':

    config = Config()
    db = Database(config)
    ser = Serial(config)

    print('SBFspot S0 bridge started')
    print('Waiting to retrieve data ...')

    while True:
        ts =  datetime.now().timestamp()

        # before minute of time is a multiple of 5 minutes
        if (int(ts) % 300) == 299:
            ts_log = roundup(ts)

            new_serial_data = ser.get_power_since_last_request()

            print(ts_log, '\t', new_serial_data, '\t', datetime.now())

        t.sleep(1)

