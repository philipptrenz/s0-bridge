#!/usr/bin/python3
"""
"""
from urllib import request
import json, time

class Network:

    def __init__(self, config):
        self.cfg = config
        self.network_config = self.cfg.get_network_config()
        self.nodes = self.network_config["nodes"]
        self.is_enabled = self.network_config["enabled"] == 'true'

        self.prev_values = [[]] * len(self.nodes)
        self.last_retrieved = [0] * len(self.nodes)

        self.unsigned_long_max_size = 2 ** 32 - 1

        self.prev_consumption = {
            "ts": -1,
            "consumption": None,
            "production": None
        }

        if self.is_enabled:
            self.get_power_since_last_request(True)


    def read_network(self, url, timeout, method="GET"):
        req = request.Request(url, method=method)
        with request.urlopen(req, timeout=timeout) as response:
            raw_data = response.read()
            data = raw_data.decode("utf-8")
            obj = json.loads(data)
            return obj

    def get_power_since_last_request(self, initial_request=False):

        res = []

        for node_idx, node in enumerate(self.nodes):

            node_name = node["node_name"]
            timeout = node["timeout"]
            interfaces = node["interfaces"]

            if "url" in node:
                url = node["url"]
            else:
                url = node["ip_address"]
                if not url.startswith('http://'): url = 'http://' + url
                if not url.endswith('/'): url += '/'
                url += 'total'

            if not initial_request: self.cfg.log('network: collecting data from node \''+node_name+'\'', url)

            diff = [0] * len(interfaces)
            new_values = []

            try:
                new_values = self.read_network(url, timeout, method=node["method"])[0:len(interfaces)]
            except Exception as e:
                if not initial_request: self.cfg.log('network: request failed', e)
                new_values = [0] * len( interfaces )



            if len(self.prev_values[node_idx]) == 0:
                self.prev_values[node_idx] = [0] * len(interfaces)

            now = time.time()

            if not self.last_retrieved[node_idx] == 0:
                for idx in range(len(interfaces)):
                    diff[idx] = new_values[idx] - self.prev_values[node_idx][idx]
                    if new_values[idx] < self.prev_values[node_idx][idx]:  # arduino unsigned long overflow
                        diff[idx] = self.unsigned_long_max_size - self.prev_values[node_idx][idx] + new_values[idx]

            self.prev_values[node_idx] = new_values

            for i_idx, source in enumerate(interfaces):

                # Only applicable for inverters
                if "type" in source and source["type"] != "inverter": continue

                power = 0
                watts = 0
                if self.last_retrieved != 0:
                    pulses = diff[i_idx]
                    watts = int(pulses / source["pulses_per_kwh"] * 1000)       # convert pulses to Wh
                    power = int(watts / (now - self.last_retrieved[node_idx]) * 3600)     # calculate avg power production in Wh

                res.append({
                    "energy": watts,
                    "power": power,
                    "source": source
                })

            self.last_retrieved[node_idx] = now

        return res


    def process_consumption(self, db, cfg):

        now = time.time()

        initial_request = self.prev_consumption["ts"] <= 0

        new_comsumption = None
        new_production = None

        offset_inverters = []

        for node_idx, node in enumerate(self.nodes):

            # Only process nodes with consumption type
            if "consumption" not in [ i["type"] if "type" in i else None for i in node["interfaces"]]: continue

            node_name = node["node_name"]
            timeout = node["timeout"]
            interfaces = node["interfaces"]

            if "url" in node:
                url = node["url"]
            else:
                url = node["ip_address"]
                if not url.startswith('http://'): url = 'http://' + url
                if not url.endswith('/'): url += '/'
                url += 'total'

            if not initial_request: self.cfg.log('network: collecting data from node \''+node_name+'\'', url)

            try:
                new_values = self.read_network(url, timeout, method=node["method"])[0:len(interfaces)]
                for i_idx, source in enumerate(interfaces):
                    val = new_values[i_idx]
                    if source["type"] == "consumption":
                        if source["reading"] != "absolute":
                            self.cfg.log('only absolute readings supported for consumption')
                            continue
                        if source["unit"] == "Wh":
                            new_comsumption = val
                        elif source["unit"] == "kWh":
                            new_comsumption = val * 1000

                    if source["type"] == "production":
                        if source["reading"] != "absolute":
                            self.cfg.log('only absolute readings supported for production')
                            continue
                        if source["unit"] == "Wh":
                            new_production = val
                        elif source["unit"] == "kWh":
                            new_production = val * 1000

                        offset_inverters = source["offset_inverters_with_serial_id"]

            except Exception as e:
                if not initial_request: self.cfg.log('network: request failed', e)
        
        if initial_request:
            self.prev_consumption = {
                "ts": now,
                "consumption": new_comsumption,
                "production": new_production
            }
            return False

        prev_ts = self.prev_consumption["ts"]
        grid_consumption = new_comsumption - self.prev_consumption["consumption"]
        pv_self_consumption = 0

        if new_production:
            diff_production = new_production - self.prev_consumption["production"]
            if len(offset_inverters) > 0:
                self_consumption_plant_production = db.get_production_in_range(start=prev_ts, end=now, inverters=offset_inverters)
                pv_self_consumption = self_consumption_plant_production - diff_production

        

        energy_used = grid_consumption + pv_self_consumption
        power_used = energy_used / (now - prev_ts) * 3600

        cfg.log("reporting consumption: " + str(energy_used) + " Wh (grid: " + str(grid_consumption) + " Wh, pv: " + str(pv_self_consumption) + " Wh)")

        db.add_consumption_data_row(now, energy_used, power_used)

        self.prev_consumption = {
            "ts": now,
            "consumption": new_comsumption,
            "production": new_production
        }

        return True


    def close(self):
        pass


if __name__ == '__main__':

    from config import Config
    from database import Database
    import time

    cfg = Config(config_path='config.json')
    ntwrk = Network(cfg)
    db = Database(cfg)

    ntwrk.process_consumption(db)

    ntwrk.process_consumption(db)

    ntwrk.process_consumption(db)


    exit()

    while True:
        data = ntwrk.get_power_since_last_request()

        s = '['
        for i, d in enumerate(data):
            s += str(d["energy"])
            if i < len(data)-1: s += ','
        s += ']'
        print(data)
        time.sleep(3)
