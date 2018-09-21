#!/usr/bin/env python3
import time as t, math
from datetime import datetime, date, time, timedelta

from util.config import Config
from util.database import Database

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100


if __name__ == '__main__':

    config = Config()
    db = Database(config=config)

    while True:
        ts =  datetime.now().timestamp()

        # before 5 minutes have elapsed
        if (int(ts) % 300) == 299:
            # execute
            ts_log = roundup(ts)
            print(ts, '\t', ts_log, '\t', datetime.fromtimestamp(ts_log), '\t', datetime.now() )

        t.sleep(1)

