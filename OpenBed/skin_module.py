import RPi.GPIO as io
import sys
import time
from math import log


class AD7171(object):
	AD7171_PATTERN = 0x0D
	AD7171_RESOLUTION = 32767.0

	def __init__(self, data_pin, sclk_pin):
		io.setwarnings(False)
		io.setmode(io.BCM)

		self.data_pin = data_pin
		self.sclk_pin = sclk_pin
		self.pattern = 0

		io.setup(self.data_pin, io.IN)
		io.setup(self.sclk_pin, io.OUT)

		io.output(self.sclk_pin, io.HIGH)

	def read(self):
		data = 0
		timeout = 0

		self.pattern = 0

		io.output(self.sclk_pin, io.HIGH)
		time.sleep(0.01)

		while True:
			data = 0

			if not io.input(self.data_pin):
				for i in range(23, -1, -1):
					io.output(self.sclk_pin, io.LOW)
					io.output(self.sclk_pin, io.HIGH)

					if io.input(self.data_pin):
						data |= (1 << i)

			if ((data & 0x1F) == self.AD7171_PATTERN) and ((data & 0x80) == 0):
				break

			if timeout >= 1000:
				break

			timeout += 1
			time.sleep(0.001)

		self.pattern = data & 0xFF

		if data & 0x800000:
			return (data >> 8) & 0x7FFF

		return 0

	def read_normalized(self):
		return float(float(self.read()) / self.AD7171_RESOLUTION)

	def is_valid(self):
		return ((self.pattern & 0x1F) == self.AD7171_PATTERN)

	def get_pattern(self):
		return self.pattern

	@staticmethod
	def get_max():
		return 32767


class SkinSensor(object):
	A = 0.001214095268
	B = 0.0002351453496
	C = 0.00000009101744098
	REF_RESISTOR = 10000.0
	T0 = 273.15

	def __init__(self, adc):
		self.adc = adc
		self.resistor = 0

	def read_resistor(self):
		self.resistor = 0

		ratio = self.adc.read_normalized()
		if not self.adc.is_valid():
			self.resistor = 0
			return 0

		if self.adc.get_pattern() & 0x20:
			self.resistor = AD7171.get_max()
		else:
			self.resistor = self.REF_RESISTOR * ratio

		return self.resistor

	def read(self):
		res = self.read_resistor()

		if not self.is_valid():
			return 0

		temp = (1.0	/ (self.A + (self.B * log(res)) + self.C * (log(res) * log(res) * log(res)))) - self.T0
		return int(temp * 100.0)

	def is_valid(self):
		if self.resistor < 100 or self.resistor > 32000:
			return False

		return True

	def get_resistor(self):
		return self.resistor