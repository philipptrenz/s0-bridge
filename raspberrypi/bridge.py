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

    while True:
        ts =  datetime.now().timestamp()

        # before 5 minutes have elapsed
        if (int(ts) % 300) == 299:
            ts_log = roundup(ts)

            newData = ser.get_power_since_last_request()
            print(ts_log, '\t', )

        t.sleep(1)

