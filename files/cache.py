from datetime import datetime, timedelta
import hashlib
import re
from itertools import repeat
from logs import Logs
class Cache:
	def __init__(self, expirationMinutes:int):
		self.expirationMinutes = expirationMinutes
		self.cache = {}
		self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
		self.groupCaseSensitive = True
		self.groupConditional = 'and'

		self.logs = Logs(self.__class__.__name__)

	def __hash__(self, text:str) -> str:
		'''
			Returns a hash from a string
		'''
		return hashlib.sha256(text.encode('utf-8')).hexdigest()

	def settings(self, groupCaseSensitive:bool, groupConditional:str):
		'''
			Initiliaze settings for the cache
		'''
		self.groupCaseSensitive = groupCaseSensitive
		self.groupConditional = groupConditional

	def addUser(self, username:str, password:str):
		'''
			Add user to the cache
		'''
		if username not in self.cache:
			self.logs.info({'message':'Adding user to the cache.', 'username': username})
			passwordHash = self.__hash__(password)
			self.cache[username] = {'password': passwordHash, 'adGroups': []}

	def addGroups(self, username:str, adGroups:list):
		'''
			Add user groups to the cache
		'''
		if username in self.cache:
			self.logs.info({'message':'Adding groups to the cache.', 'username': username})
			self.cache[username]['adGroups'] = adGroups

	def validateUser(self, username:str, password:str) -> bool:
		'''
			Validate user from cache
			Returns True if the username and password are correct, False otherwise
		'''
		if self.validUntil < datetime.now():
			self.logs.info({'message':'Cache expired.'})
			self.cache = {}
			self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
			return False

		if username in self.cache:
			self.logs.info({'message':'Validating user via cache.', 'username': username})
			passwordHash = self.__hash__(password)
			if passwordHash == self.cache[username]['password']:
				self.logs.info({'message':'Username and password validated by cache.', 'username': username})
				return True
			else:
				self.logs.warning({'message':'Invalid password from cache, invalidating cache.', 'username': username})
				del self.cache[username]
				return False

		self.logs.info({'message':'User not found in the cache for authentication.', 'username': username})
		return False

	def __findMatch__(self, group:str, adGroup:str):
		try:
			# Extract the Common Name from the string (letters, spaces, underscores and hyphens)
			adGroup = re.search('(?i)CN=((\w*\s?_?-?)*)', adGroup).group(1)
		except Exception as e:
			self.logs.warning({'message':'There was an error trying to search CN: %s' % e})
			return None

		# Disable case sensitive
		if not self.groupCaseSensitive:
			adGroup = adGroup.lower()
			group = group.lower()

		# Return match against supplied group/pattern (None if there is no match)
		try:
			return re.fullmatch(f'{group}.*', adGroup).group(0)
		except:
			return None

	def validateGroups(self, username:str, groups:list):
		'''
			Validate user's groups
			Returns True if the groups are valid for the user, False otherwise
		'''
		if username in self.cache:
			adGroups = self.cache[username]['adGroups']

			self.logs.info({'message':'Validating groups from cache.', 'username': username, 'groups': ','.join(groups), 'conditional': self.groupConditional})
			matchedGroups = []
			matchesByGroup = []
			for group in groups:
				matches = list(filter(None,list(map(self.__findMatch__, repeat(group), adGroups))))
				if matches:
					matchesByGroup.append((group,matches))
					matchedGroups.extend(matches)

			# Conditional OR, true if just 1 group match
			if self.groupConditional == 'or':
				if len(matchedGroups) > 0:
					self.logs.info({'message':'At least one group from cache is valid for the user.', 'username': username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
					return True,matchedGroups
			# Conditional AND, true if all the groups match
			elif self.groupConditional == 'and':
				if len(groups) == len(matchesByGroup):
					self.logs.info({'message':'All groups from cache are valid for the user.', 'username': username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
					return True,matchedGroups
			else:
				self.logs.error({'message':'Invalid conditional group.', 'username': username, 'conditional': self.groupConditional})
				return False,[]

			self.logs.warning({'message':'Invalid groups from cache.', 'username': username, 'conditional': self.groupConditional})
			return False,[]

		self.logs.info({'message':'User not found in the cache for validate groups.', 'username': username})
		return False,[]