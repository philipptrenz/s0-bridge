#!/usr/bin/python3
"""
"""
import json, os.path
from datetime import datetime

class Config():

    def __init__(self, config_path=None):
        self.config = dict()
        if config_path is not None:
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            try:
                with open('config.json') as f:
                    self.config = json.load(f)
            except:
                with open('config.default.json') as f:
                    self.config = json.load(f)

    def print(self):
        print(self.config)

    def get_config(self):
        return self.config

    def get_database_path(self):
        path = self.config["database"]["path"]
        if os.path.isfile(path):
            return self.config["database"]["path"]
        else:
            raise Exception("sqlite database %s does not exist, check the config(.default).json!" % path)

    def get_serial_config(self):
        return self.config["data_interfaces"]["serial"]

    def get_network_config(self):
        return self.config["data_interfaces"]["network"]

    def get_connection_interfaces(self):
        interfaces = list()
        if "interfaces" in self.config["data_interfaces"]["serial"]:
            interfaces.extend(self.config["data_interfaces"]["serial"]["interfaces"])
        if "interfaces" in self.config["data_interfaces"]["network"]:
            interfaces.extend(self.config["data_interfaces"]["network"]["interfaces"])
        return interfaces

    def log(self, msg, error=''):
        ts = datetime.now()
        if error: print(ts, '|', msg, '['+str(error)+']')
        else: print(ts, '|', msg)