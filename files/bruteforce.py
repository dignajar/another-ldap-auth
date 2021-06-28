from datetime import datetime, timedelta
from logs import Logs
from security import Security

class BruteForce:
	def __init__(self, enabled:bool, expirationSeconds:int, blockAfterFailures:int):
		self.database = {}
		self.enabled = enabled
		self.expirationSeconds = expirationSeconds
		self.blockAfterFailures = blockAfterFailures
		self.logs = Logs(self.__class__.__name__)
		self.security = Security()

	def addFailure(self):
		'''
			Increase IP failure
		'''
		# Check if brute force protection is enabled
		if not self.enabled:
			return False

		ip = self.security.getUserIp()

		# Check if this is the first time that the IP will be in the database
		if ip not in self.database:
			self.logs.info({'message':'Start IP failure counter.', 'ip': ip, 'failures': '1'})
			blockUntil = datetime.now() + timedelta(seconds=self.expirationSeconds)
			self.database[ip] = {'counter': 1, 'blockUntil': blockUntil}
		else:
			# Check if the IP expire and renew the database for that IP
			if self.database[ip]['blockUntil'] < datetime.now():
				self.logs.info({'message':'IP failure counter expired, removing IP...', 'ip': ip})
				del self.database[ip]
				self.addFailure(ip)
				return False

			# The IP is already in the database, increase the failure counter
			self.database[ip]['counter'] = self.database[ip]['counter'] + 1
			self.logs.info({'message':'Increase IP failure counter.', 'ip': ip, 'failures': str(self.database[ip]['counter'])})

			# The IP already match the amount of failures, block the IP
			if self.database[ip]['counter'] >= self.blockAfterFailures:
				self.database[ip]['blockUntil'] = datetime.now() + timedelta(seconds=self.expirationSeconds)
				self.logs.warning({'message':'IP blocked.', 'ip': ip, 'blockUntil': str(self.database[ip]['blockUntil'])})

		return False

	def isIpBlocked(self) -> bool:
		'''
			Returns True if the IP is blocked, False otherwise
		'''
		# Check if brute force protection is enabled
		if not self.enabled:
			return False

		ip = self.security.getUserIp()

		if ip not in self.database:
			self.logs.info({'message':'The IP is not in the database and is not blocked.', 'ip': ip})
			return False

		# The IP is on the database, check the amount of failures
		if self.database[ip]['counter'] >= self.blockAfterFailures:
			self.logs.warning({'message':'The IP is blocked.', 'ip': ip, 'blockUntil': str(self.database[ip]['blockUntil'])})

			# Check if the IP expire and remove from the database
			if self.database[ip]['blockUntil'] < datetime.now():
				self.logs.warning({'message':'Removing IP from the database, lucky guy, time expired.', 'ip': ip})
				del self.database[ip]
				return False
			return True

		self.logs.info({'message':'The IP is not blocked.', 'ip': ip})
		return False
