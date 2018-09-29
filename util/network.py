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
        self.is_enabled = self.network_config["enabled"]

        self.prev_values = [[]] * len(self.nodes)
        self.last_retrieved = [0] * len(self.nodes)

        self.unsigned_long_max_size = 2 ** 32 - 1

        if self.is_enabled:
            self.get_power_since_last_request(True)


    def read_network(self, url, timeout):
        req = request.Request(url)
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

            url = node["ip_address"]
            if not url.startswith('http://'): url = 'http://' + url
            if not url.endswith('/'): url += '/'
            url += 'total'

            if not initial_request: self.cfg.log('network: collecting data from node \''+node_name+'\'', url)

            diff = [0] * len(interfaces)
            new_values = []

            try:
                new_values = self.read_network(url, timeout)[0:len(interfaces)]
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


    def close(self):
        self.conn.close()


if __name__ == '__main__':

    from config import Config
    import time

    cfg = Config(config_path='../config.json')
    ntwrk = Network(cfg)

    while True:
        data = ntwrk.get_power_since_last_request()

        s = '['
        for i, d in enumerate(data):
            s += str(d["energy"])
            if i < len(data)-1: s += ','
        s += ']'
        print(data)
        time.sleep(3)