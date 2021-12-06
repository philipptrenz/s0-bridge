#!/usr/bin/python3
"""
"""
import sqlite3, pytz
from datetime import datetime, timedelta


class Database():

    def __init__(self, config):
        self.config = config
        self.db = sqlite3.connect(self.config.get_database_path(), check_same_thread=False)
        self.c = self.db.cursor()

    def add_inverters(self):
        interfaces = self.config.get_connection_interfaces()
        for source in interfaces:
            if source["type"] == "inverter" and len(source["serial_id"]) > 0:

                query = '''
                    INSERT OR IGNORE INTO Inverters (
                        Serial,
                        EToday,
                        ETotal
                    ) VALUES (
                        ?,
                        ?,
                        ?
                    );
                '''
                self.c.execute(query, (source["serial_id"], 0, source["prev_etotal"]))

                query = '''
                    UPDATE Inverters
                    SET
                        Name=?,
                        Type=?,
                        SW_Version=?,
                        Status=?,
                        TimeStamp=?
                    WHERE Serial=?;
                '''
                self.c.execute(query, (source["name"], source["inverter_type"], "s0-bridge v0", "OK", int(datetime.now().timestamp()), source["serial_id"] ))

                self.db.commit()

    def add_data(self, ts, data_points):
        for data in data_points:

            data_type = data['source']['type']

            if data_type == 'inverter':

                self.add_inverter_data(ts, data)

            elif data_type == 'consumption':

                self.add_consumption_data_row(ts, data['energy'], data['power'])

    def add_inverter_data(self, ts, data):

        inv_serial = data['source']['serial_id']
        prev_ts, prev_etoday, prev_etotal = self.get_previous_yields(inv_serial)

        status = 'OK'  # TODO: Generate actual status value

        self.add_day_data_row(ts, data, prev_etotal)

        if self.is_timestamps_from_same_day(prev_ts, ts):

            self.update_inverter(inv_serial, ts, status, prev_etoday + data['energy'],  prev_etotal + data['energy'])

        else:   # is new day

            self.update_inverter(inv_serial, ts, status, data['energy'],  prev_etotal + data['energy'])
            self.add_month_data_row(inv_serial, ts, prev_etoday, prev_etotal)

        self.db.commit()

    def add_day_data_row(self, ts, data, prev_etotal):

        if data['power'] > 0:

            inv_serial = data['source']['serial_id']
            query = '''
               INSERT INTO DayData (
                   TimeStamp,
                   Serial,
                   Power,
                   TotalYield
               ) VALUES (
                   ?,
                   ?,
                   ?,
                   ?
               );
            '''
            self.c.execute(query, (ts, inv_serial, data['power'],  prev_etotal + data['energy']))


    def get_previous_yields(self, inverter_serial):
        query = '''
           SELECT TimeStamp, EToday, ETotal
           FROM Inverters
           WHERE Serial=?
        '''
        self.c.execute(query, (inverter_serial,))
        data = self.c.fetchone()
        return data[0], data[1], data[2]

    def update_inverter(self, inverter_serial, ts, status, etoday, etotal):
        query = '''
            UPDATE Inverters
            SET
                TimeStamp=?,
                Status=?,
                eToday=?,
                eTotal=?
            WHERE Serial=?;
        '''
        self.c.execute(query, (ts, status, etoday, etotal, inverter_serial))

    def add_month_data_row(self, inverter_serial, ts, etoday, etotal):

        y = datetime.fromtimestamp(ts) - timedelta(days=1)
        y_ts = int(datetime(y.year, y.month, y.day, 23, tzinfo=pytz.utc).timestamp())

        query = '''
            INSERT INTO MonthData (
                TimeStamp,
                Serial,
                DayYield,
                TotalYield
            ) VALUES (
                ?,
                ?,
                ?,
                ?
            );
        '''
        self.c.execute(query, (y_ts, inverter_serial, etoday, etotal))

    def add_consumption_data_row(self, ts, energy_used, power_used):

        if power_used <= 0: return

        query = '''
            INSERT OR IGNORE INTO Consumption (
                TimeStamp,
                EnergyUsed,
                PowerUsed
            ) VALUES (
                ?,
                ?,
                ?
            );
        '''
        self.c.execute(query, (int(ts), 0, 0))


        query = '''
            UPDATE Consumption SET
            EnergyUsed = EnergyUsed + ?,
            PowerUsed = PowerUsed + ?
            WHERE TimeStamp=?;
        '''

        self.c.execute(query, (int(energy_used), int(power_used), int(ts)))

        self.db.commit()



    def is_timestamps_from_same_day(self, ts1, ts2):
        d1 = datetime.fromtimestamp(ts1)
        d2 = datetime.fromtimestamp(ts2)
        return (d1.year == d2.year and d1.month == d2.month and d1.day == d2.day)


    def get_production_in_range(self, start, end, inverters):
        # Returns production in watts

        query = '''
           SELECT MAX(TotalYield)-MIN(TotalYield)
           FROM DayData WHERE Serial IN ({seq})
           AND TimeStamp BETWEEN ? AND ? GROUP BY Serial;
        '''.format(seq=','.join(['?']*len(inverters)))

        args = inverters.copy()
        args.append(int(start))
        args.append(int(end))

        self.c.execute(query, args)
        data = self.c.fetchall()

        #print(query, args, data)

        if(len(data) > 0):
            sum = 0.0
            for d in data:
                if type(d) == int: sum += d
                else: sum += d[0]
            return sum
        return 0

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
        test_data = [
            {
                'energy': int(watts),
                'power': int(watts / 5*60),
                'source': {
                    "serial_id": "1000000001",
                    "name": "TEST PLANT",
                    "type": "inverter",
                    "prev_etotal": 62,
                    "pulses_per_kwh": 1000
                }
            },
            {
                'energy': int(watts),
                'power': int(watts / 5 * 60),
                'source': {
                    "serial_id": "1000000002",
                    "name": "TEST CONSUMPTION COUNTER",
                    "type": "consumption"
                }
            }
        ]

        db.add_data(test_ts, test_data)
        print(test_date.strftime("%y-%m-%d %H:%M:%S"), '\t', test_ts, '\t', test_data[0]['energy'], '\t', test_data[0]['power'])

        time.sleep(0.1)