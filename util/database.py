#!/usr/bin/python3
"""
"""
import sqlite3, json, pytz
from datetime import datetime, timedelta


class Database():

    def __init__(self, config):
        self.config = config
        self.db = sqlite3.connect(self.config.get_database_path(), check_same_thread=False)
        self.c = self.db.cursor()

    def add_inverters(self):
        interfaces = self.config.get_connection_interfaces()
        for inv in interfaces:
            if inv["type"] == "inverter":

                query = '''
                    INSERT OR IGNORE INTO Inverters (
                        Serial,
                        EToday,
                        ETotal
                    ) VALUES (
                        %s,
                        %s,
                        %s
                    );
                ''' % (inv["serial_id"], 0, inv["prev_etotal"])
                self.c.execute(query)

                query = '''
                    UPDATE Inverters
                    SET     
                        Name='%s', 
                        Type='%s', 
                        SW_Version='%s', 
                        Status='%s',
                        TimeStamp='%s'
                    WHERE Serial='%s';
                ''' % (inv["name"], "S0 bridge", "v0", "OK", int(datetime.now().timestamp()), inv["serial_id"] )
                self.c.execute(query)

                self.db.commit()

    def add_day_data_rows(self, ts, data):
        for d in data:

            if d['power'] < 1: continue # dont log 0 values
            inv_serial = d['inverter']['serial_id']
            last_ts, etoday, etotal = self.get_previous_yields(inv_serial)

            new_etotal = etotal + d['watts']

            query = '''
               INSERT INTO DayData (
                   TimeStamp,
                   Serial,
                   Power,
                   TotalYield
               ) VALUES (
                   %s,
                   %s,
                   %s,
                   %s
               );
            ''' % (ts, inv_serial, d['power'], new_etotal)
            self.c.execute(query)

            status = 'OK' # TODO: Get actual status value

            if self.is_timestamps_from_same_day(last_ts, ts):
                self.update_inverter(inv_serial, ts, status, etoday + d['watts'], new_etotal)
            else:   # is new day
                self.update_inverter(inv_serial, ts, status, d['watts'], new_etotal)
                self.add_month_data_row(inv_serial, ts, etoday, etotal)

        self.db.commit()


    def get_previous_yields(self, inverter_serial):
        query = '''
           SELECT TimeStamp, EToday, ETotal
           FROM Inverters
           WHERE Serial = '%s'
        ''' % (inverter_serial)
        self.c.execute(query)
        data = self.c.fetchone()
        return data[0], data[1], data[2]

    def update_inverter(self, inverter_serial, ts, status, etoday, etotal):
        query = '''
            UPDATE Inverters
            SET     
                TimeStamp='%s', 
                Status='%s', 
                eToday='%s',
                eTotal='%s'
            WHERE Serial='%s';
        ''' % (ts, status, etoday, etotal, inverter_serial)
        self.c.execute(query)

    def add_month_data_row(self, inverter_serial, ts, etoday, etotal):

        print('MonthData', '\t', datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M"), '\t', test_ts, '\t', etoday, '\t',
              etotal)
        y = datetime.fromtimestamp(ts) - timedelta(days=1)
        y_ts = int(datetime(y.year, y.month, y.day, 23, tzinfo=pytz.utc).timestamp())

        query = '''
            INSERT INTO MonthData (
                TimeStamp,
                Serial,
                DayYield,
                TotalYield                                 
            ) VALUES (
                %s,
                %s,
                %s,
                %s
            );
        ''' % (y_ts, inverter_serial, etoday, etotal)
        self.c.execute(query)

    def is_timestamps_from_same_day(self, ts1, ts2):
        d1 = datetime.fromtimestamp(ts1)
        d2 = datetime.fromtimestamp(ts2)
        return (d1.year == d2.year and d1.month == d2.month and d1.day == d2.day)

    def get_epoch(self, date):
        s = date.split('-')
        return int(datetime(int(s[0]), int(s[1]), int(s[2]), 00, 00, 00, tzinfo=pytz.utc).timestamp())

    def get_epoch_day(self, date):
        #s = date.split('-')
        #epoch_start =  int(datetime(int(s[0]), int(s[1]), int(s[2]), 00, 00, 00, tzinfo=pytz.utc).timestamp())
        #epoch_end =  int(datetime(int(s[0]), int(s[1]), int(s[2]), 23, 59, 59, tzinfo=pytz.utc).timestamp())
        epoch_start = int(datetime(date.year, date.month, date.day, 00, 00, 00, tzinfo=pytz.utc).timestamp())
        epoch_end = int(datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=pytz.utc).timestamp())
        return epoch_start, epoch_end

    def get_epoch_month(self, date):
        s = date.split('-')
        epoch_start = int(datetime(int(s[0]), int(s[1]), 1, 00, 00, 00, tzinfo=pytz.utc).timestamp())
        epoch_end = int(datetime(int(s[0]), int(s[1]), self.get_last_day_of_month(date), 23, 59, 59, tzinfo=pytz.utc).timestamp())
        return epoch_start, epoch_end

    def get_last_day_of_month(self, date):
        day = datetime.strptime(date, "%Y-%m-%d")
        next_month = day.replace(day=28) + timedelta(days=4)  # this will never fail
        return (next_month - timedelta(days=next_month.day)).day



    def close(self):
        self.db.close()

if __name__ == '__main__':
    #print('nothing to do here')

    import random, time
    from config import Config

    cfg = Config(config_path='../config.json')
    db  = Database(cfg)

    db.add_inverters()

    test_ts = 1535932800

    print(test_ts)

    while True:

        test_ts += 300
        test_date = datetime.fromtimestamp(test_ts)

        if test_date.hour in range(0, 8) or test_date.hour in range(18, 24): continue

        watts = random.randint(50, 400)
        test_data = [{
            'watts': int(watts),
            'power': int(watts / 5*60),
            'inverter': {
                "serial_id": "1000000001",
                "name": "TEST PLANT",
                "type": "inverter",
                "prev_etotal": 62,
                "pulses_per_kwh": 1000
            }
        }]

        db.add_day_data_rows(test_ts, test_data)
        print(test_date.strftime("%y-%m-%d %H:%M"), '\t', test_ts, '\t', test_data[0]['watts'], '\t', test_data[0]['power'])

        time.sleep(0.1)





