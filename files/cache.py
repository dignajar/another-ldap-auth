from logs import Logs
from datetime import datetime, timedelta
import hashlib

class Cache:
	def __init__(self, expirationMinutes):
		self.expirationMinutes = expirationMinutes
		self.cache = {}
		self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
		self.logs = Logs()

	# Returns a sha256 hash
	def hash(self, text):
		return hashlib.sha256(text.encode('utf-8')).hexdigest()

	# Add user to the cache
	def addUser(self, username, password):
		if username not in self.cache:
			self.logs.info({'message':'Adding user to the cache.', 'username': username})
			passwordHash = self.hash(password)
			self.cache[username] = {'password': passwordHash, 'groups': ''}

	# Add groups to the cached user
	def addGroups(self, username, groups):
		if username in self.cache:
			self.cache[username]['groups'] = groups

	# Validate user from cache
	# Returns True if the username and password are correct, False otherwise
	def validateUser(self, username, password):
		if self.validUntil < datetime.now():
			self.logs.info({'message':'Cache expired.'})
			self.cache = {}
			self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
			return False

		if username in self.cache:
			self.logs.info({'message':'User found in the cache.', 'username': username})
			passwordHash = self.hash(password)
			if passwordHash == self.cache[username]['password']:
				self.logs.info({'message':'Username and password validated by cache.', 'username': username})
				return True
			else:
				self.logs.warning({'message':'Invalid password from cache, invalidating cache.', 'username': username})
				del self.cache[username]
				return False

		self.logs.info({'message':'User not found in the cache.', 'username': username})
		return False

