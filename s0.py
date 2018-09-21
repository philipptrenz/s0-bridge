#!/usr/bin/env python3

import time, serial, json, threading
from datetime import datetime, timedelta

interval = 30 # seconds
last = 0

def read_serial():
	ser.write(bytearray('t','ascii')) # trigger arduino to deliver data

	while (ser.inWaiting() == 0):
		time.sleep(0.01)
	data = ser.readline().decode("utf-8")

	return json.loads(data)

def log(meter_readings):
	global last

	current_power = ''
	if (last is not 0):
		current_power = str('%.2f' % ((meter_readings[0]-last) / 1000 * (3600 / interval) )) + ' kWh'

	log_str = str(datetime.now())+'\t'+json.dumps(meter_readings)+'\t'+current_power
	print(log_str)
	with open('s0_log.txt', 'a') as out:
		out.write(log_str+'\n')

	last = sum(meter_readings)

if __name__ == '__main__':

	ser = serial.Serial(
		'/dev/serial0',
		baudrate=115200
	)

	time.sleep(1)

	try:

		# retrieve data from ATmega328P every 30 seconds
		while True:
			meter_readings = read_serial()
			log(meter_readings)
			
			time.sleep(interval)
			
	except KeyboardInterrupt:
		print("Exiting program")
	except Exception as e:
		print("Error occured", e)
	finally:
		ser.close()
		pass

