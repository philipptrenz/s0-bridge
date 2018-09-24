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
                        Serial
                    ) VALUES (
                        %s
                    );
                ''' % (inv["serial_id"])
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

    def update_inverter(self, serial, ts, status, etoday, etotal):
        query = '''
            UPDATE Inverters
            SET     
                TimeStamp='%s', 
                Status='%s', 
                eToday='%s',
                eTotal='%s'
            WHERE Serial='%s';
        ''' % (ts, status, etoday, etotal, serial)
        self.c.execute(query)

    def add_day_data_rows(self, ts, data):
        for d in data:
            prev_total_yield = self.get_previous_total_yield(d["inverter"])
            new_total_yield = prev_total_yield + d['watts']
            prev_todays_yield = self.get_previous_todays_yield(ts, d['inverter'])
            new_todays_yield = prev_todays_yield + d['watts']

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
            ''' % (ts, d['inverter']['serial_id'], d['power'], new_total_yield)
            self.c.execute(query)

            status = 'OK' # TODO

            self.update_inverter(d['inverter']['serial_id'], ts, status, new_todays_yield, (prev_total_yield + d['watts']))

        self.db.commit()

    def get_previous_total_yield(self, inverter):
        # get power of last data point
        query = '''
           SELECT TotalYield 
           FROM DayData
           WHERE TimeStamp = (
               SELECT MAX(TimeStamp)
               FROM DayData
               WHERE Serial = %s
           )
        '''
        self.c.execute(query % (inverter['serial_id']))
        prev_datapoint = self.c.fetchone()
        if prev_datapoint is not None:
            return prev_datapoint[0]
        else:
            return inverter['prev_etotal']

    def get_previous_todays_yield(self, ts, inverter):
        query = '''
            SELECT TimeStamp, EToday
            FROM Inverters
            WHERE Serial = %s;
        ''' % inverter['serial_id']
        self.c.execute(query)
        row = self.c.fetchone()
        if row[0] is not None and row[1] is not None and self.is_timestamps_from_same_day(ts, row[0]):
            return row[1]
        else: return 0 # is new day or has no previous data

    def add_month_data_rows(self, data):

        for d in data:
            inv_serial = d['inverter']['serial_id']
            y = datetime.now() - timedelta(days=1)
            yesterday_start, yesterday_end = self.get_epoch_day(y)

            query = '''
                 SELECT * 
                 FROM MonthData 
                 WHERE Serial = %s AND TimeStamp BETWEEN %s AND %s;
             ''' % (inv_serial, yesterday_start, yesterday_end)
            self.c.execute(query)

            if self.c.fetchone() is None:  # entry is missing

                y_ts = int(datetime(y.year, y.month, y.day, 23, tzinfo=pytz.utc).timestamp())

                query = '''
                     SELECT SUM(Power) FROM DayData WHERE Serial = %s AND TimeStamp BETWEEN %s AND %s;
                 ''' % (inv_serial, yesterday_start, yesterday_end)
                self.c.execute(query)
                sum_power = 0
                fetched = self.c.fetchone()[0]
                if fetched is not None:
                    sum_power = fetched / 60 * 5  # normalize 5 min power back to hour

                query = '''
                     INSERT INTO MonthData (
                         TimeStamp,
                         Serial,
                         TotalYield,
                         DayYield
                     ) VALUES (
                         %s,
                         %s,
                         (SELECT MAX(TotalYield) FROM DayData WHERE Serial = %s AND TimeStamp BETWEEN %s AND %s),
                         %s
                     );
                 ''' % (y_ts, inv_serial, inv_serial, yesterday_start, yesterday_end, sum_power)

                self.c.execute(query)

        self.db.commit()

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
    print('nothing to do here')

    #print(datetime(2018,9,15, 0, tzinfo=pytz.utc).timestamp())



    s = datetime(2018,9,13, 0, tzinfo=pytz.utc)
    epoch_start = int(datetime(2018,9,15, 00, 00, 00, tzinfo=pytz.utc).timestamp())
    epoch_end = int(datetime(2018,9,15, 23, 59, 59, tzinfo=pytz.utc).timestamp())
    print(epoch_start, epoch_end)

    i = 1537781571
    d = datetime.fromtimestamp(i)
    print(d)





