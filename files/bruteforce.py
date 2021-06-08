from datetime import datetime, timedelta
from logs import Logs
from flask import request

class BruteForce:
	def __init__(self, enabled:bool, expirationMinutes:int, blockAfterFailures:int):
		self.database = {}
		self.enabled = enabled
		self.expirationMinutes = expirationMinutes
		self.blockAfterFailures = blockAfterFailures
		self.logs = Logs(self.__class__.__name__)

	def addFailure(self):
		'''
			Increase IP failure
		'''
		if not self.enabled:
			return False

		ip = request.remote_addr

		if ip not in self.database:
			self.logs.info({'message':'Adding IP to the brute force database.', 'ip': ip})
			self.database[ip] = {'counter': 1, 'blockUntil': 0}
		else:
			self.database[ip]['counter'] = self.database[ip]['counter'] + 1
			self.logs.info({'message':'Increased IP failure counter.', 'ip': ip, 'failures': str(self.database[ip]['counter'])})

			if self.database[ip]['counter'] >= self.blockAfterFailures:
				self.database[ip]['blockUntil'] = datetime.now() + timedelta(minutes=self.expirationMinutes)
				self.logs.warning({'message':'IP blocked.', 'ip': ip, 'blockUntil': str(self.database[ip]['blockUntil'])})

	def isBlocked(self) -> bool:
		'''
			Returns True if the IP is blocked, False otherwise
		'''
		if not self.enabled:
			return False

		ip = request.remote_addr

		if ip not in self.database:
			self.logs.info({'message':'The IP is not in the database and is not blocked.', 'ip': ip})
			return False

		if self.database[ip]['counter'] >= self.blockAfterFailures:
			self.logs.warning({'message':'The IP is blocked.', 'ip': ip, 'blockUntil': str(self.database[ip]['blockUntil'])})
			if self.database[ip]['blockUntil'] < datetime.now():
				self.logs.warning({'message':'Removing IP from the database, lucky guy, time expired.', 'ip': ip})
				del self.database[ip]
				return False
			return True

		self.logs.info({'message':'The IP is not blocked.', 'ip': ip})
		return False