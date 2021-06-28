from datetime import datetime
from flask import request
from os import environ
import json
from security import Security

class Logs:
	def __init__(self, objectName):
		self.level = 'INFO'
		if "LOG_LEVEL" in environ:
			self.level = environ["LOG_LEVEL"]

		self.format = 'TEXT'
		if "LOG_FORMAT" in environ:
			self.format = environ["LOG_FORMAT"]

		self.objectName = objectName
		self.security = Security()

	def __print__(self, level, extraFields):
		fields = {
			'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			'level': level,
			'objectName': self.objectName,
			'ip': self.security.getUserIP(),
			'referrer': self.security.getUserReferrer()
		}

		# Include extra fields custom by the user
		fields.update(extraFields)

		if self.format == 'JSON':
			print(json.dumps(fields))
		else:
			print(' - '.join(map(str, fields.values())))

	def error(self, extraFields):
		if self.level in ['INFO', 'WARNING', 'ERROR']:
			self.__print__('ERROR',extraFields)

	def warning(self, extraFields):
		if self.level in ['INFO', 'WARNING']:
			self.__print__('WARNING',extraFields)

	def info(self, extraFields):
		if self.level in ['INFO']:
			self.__print__('INFO',extraFields)