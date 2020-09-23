import logging
import hashlib
from datetime import datetime, timedelta

class Cache:
	def __init__(self, expirationMinutes):
		self.expirationMinutes = expirationMinutes
		self.cache = {}
		self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
		self.log = logging.getLogger('CACHE')

    # Add username, password and groups to cache
	def add(self, username, password, groups):
		self.log.info(f"Caching username: {username}")
		passwordHash = hashlib.md5(password.encode()).hexdigest()
		self.cache[username] = [passwordHash, groups]

	# Validate if the username has the same password
	# Also check if the cache still valid
	def validate(self, username, password, groups):
		if (self.validUntil < datetime.now()):
			self.log.info("Cache expired.")
			self.cache = {}
			self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)

		if username in self.cache:
			self.log.info(f"username found in cache: {username}")
			passwordHash = hashlib.md5(password.encode()).hexdigest()
			if self.cache[username][0] == passwordHash:
				self.log.info(f"username valid: {username}")
				if not groups:
					return True
				if self.cache[username][1] == groups: # Como validamos grupos por fuera del AD ?
					self.log.info(f"groups valid: {username}")
					return True

		self.log.info(f"username not found in cache: {username}")
		return False