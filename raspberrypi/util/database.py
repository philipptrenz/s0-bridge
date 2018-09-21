#!/usr/bin/python3
"""
"""
import sqlite3, json
from datetime import datetime, date, time, timedelta

class Database():

    def __init__(self, config):
        self.config = config
        self.db = sqlite3.connect(self.config.get_database_path(), check_same_thread=False)
        self.c = self.db.cursor()



if __name__ == '__main__':
    print('nothing to do here')

