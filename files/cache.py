from datetime import datetime, timedelta

class Cache:
	def __init__(self, expirationMinutes):
                self.expirationMinutes = expirationMinutes
                self.cache = {}
                self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)

        # Add a key and value to the cache
	def add(self, key, value):
                print("[INFO][CACHE] Caching key:", key)
                self.cache[key] = value

        # Validate if the key has the same value
        # Also check if the cache still valid
	def validate(self, key, value):
		if (self.validUntil < datetime.now()):
			print("[INFO][CACHE] Cache expired.")
			self.cache = {}
			self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)

		if key in self.cache:
			print("[INFO][CACHE] Key found in cache:", key)
			if self.cache[key] == value:
				print("[INFO][CACHE] Key valid:", key)
				return True

		print("[INFO][CACHE] Key not found in cache:", key)
		return False