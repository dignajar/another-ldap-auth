from datetime import datetime
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
		# These are the fields are printed all the time in each log line, in the following order.
		mandatoryFields = {
			'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			'level': self.level,
			'objectName': self.objectName,
			'ip': '',
			'referrer': ''
		}
		# Try to get IP and referrer from user
		try:
			mandatoryFields['ip'] = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
			mandatoryFields['referrer'] = request.headers.get("Referer")
		except Exception as e:
			pass

		# Merge dictionaries
		mandatoryFields.update(fields)

		if self.format == 'JSON':
			print(json.dumps(mandatoryFields))
		else:
			print(' - '.join(map(str, mandatoryFields.values())))

	def error(self, fields):
		if self.level in ['INFO', 'WARNING', 'ERROR']:
			self.__print__(fields)

	def warning(self, fields):
		if self.level in ['INFO', 'WARNING']:
			self.__print__(fields)

	def info(self, fields):
		if self.level in ['INFO']:
			self.__print__(fields)