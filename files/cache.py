import logging
from datetime import datetime, timedelta

class Cache:
	def __init__(self, expirationMinutes):
		self.expirationMinutes = expirationMinutes
		self.cache = {}
		self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
		self.log = logging.getLogger('CACHE')

        # Add a key and value to the cache
	def add(self, key, value):
		self.log.info(f"Caching key: {key}")
		self.cache[key] = value

        # Validate if the key has the same value
        # Also check if the cache still valid
	def validate(self, key, value):
		if (self.validUntil < datetime.now()):
			self.log.info("Cache expired.")
			self.cache = {}
			self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)

		if key in self.cache:
			self.log.info(f"Key found in cache: {key}")
			if self.cache[key] == value:
				self.log.info(f"Key valid: {key}")
				return True

		self.log.info(f"Key not found in cache: {key}")
		return False