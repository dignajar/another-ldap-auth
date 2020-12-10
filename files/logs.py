from datetime import datetime, timedelta
from flask import request
from os import environ
import json

class Logs:
	def __init__(self, objectName):
		self.level = 'INFO'
		if "LOG_LEVEL" in environ:
			self.level = environ["LOG_LEVEL"]

		self.format = 'TEXT'
		if "LOG_FORMAT" in environ:
			self.format = environ["LOG_FORMAT"]

		self.objectName = objectName

	def __print__(self, fields):
		fields['level'] = self.level
		fields['objectName'] = self.objectName
		fields['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		# Try to get IP and referrer from user
		try:
			fields['ip'] = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
			fields['referrer'] = request.headers.get("Referer")
		except Exception as e:
			pass

		if self.format == 'JSON':
			print(json.dumps(fields))
		else:
			print(" - ".join(fields.values()))

	def error(self, fields):
		if self.level in ['INFO', 'WARNING', 'ERROR']:
			self.__print__(fields)

	def warning(self, fields):
		if self.level in ['INFO', 'WARNING']:
			self.__print__(fields)

	def info(self, fields):
		if self.level in ['INFO']:
			self.__print__(fields)