import ldap
import time
import re
from itertools import repeat
from logs import Logs

class Aldap:
	def __init__(self, ldapEndpoint, dnUsername, dnPassword, serverDomain, searchBase, searchFilter, groupCaseSensitive, groupConditional):
		self.ldapEndpoint = ldapEndpoint
		self.searchBase = searchBase
		self.dnUsername = dnUsername
		self.dnPassword = dnPassword
		self.serverDomain = serverDomain
		self.searchFilter = searchFilter
		self.username = ''
		self.password = ''
		self.groupCaseSensitive = groupCaseSensitive
		self.groupConditional = groupConditional.lower()

		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		self.connect = ldap.initialize(self.ldapEndpoint)
		self.connect.set_option(ldap.OPT_REFERRALS, 0)
		self.connect.set_option(ldap.OPT_DEBUG_LEVEL, 255)

		self.logs = Logs(self.__class__.__name__)

	# Initialize the ALDAP object with the username and password
	def setUser(self, username, password):
		self.username = username
		self.password = password
		# Replace in the filter the variable "{username}" for the username
		self.searchFilter = self.searchFilter.replace("{username}", self.username)

	# Authenticate user by "username" and "password"
	# Returns True if the user is valid
	# Returns False if the user is invalid or there was a connectivy issue
	def authenticateUser(self):
		finalUsername = self.username
		if self.serverDomain:
			finalUsername = self.username+"@"+self.serverDomain

		self.logs.info({'message':'Authenticating user.', 'username': self.username, 'finalUsername': finalUsername})

		start = time.time()
		try:
			self.connect.simple_bind_s(finalUsername, self.password)
			#self.connect.unbind_s()
			end = time.time()-start
			self.logs.info({'message':'Authentication successful.', 'username': self.username, 'elapsedTime': str(end)})
			return True
		except ldap.INVALID_CREDENTIALS:
			self.logs.warning({'message':'Invalid credentials.', 'username': self.username})
		except ldap.LDAPError as e:
			self.logs.error({'message':'There was an error trying to bind: %s' % e})

		return False

	def getTree(self):
		result = ""
		try:
			start = time.time()
			self.connect.simple_bind_s(self.dnUsername, self.dnPassword)
			result = self.connect.search_s(self.searchBase, ldap.SCOPE_SUBTREE, self.searchFilter)
			#self.connect.unbind_s()
			end = time.time()-start
			self.logs.info({'message':'Search by filter.', 'filter': self.searchFilter, 'elapsedTime': str(end)})
		except ldap.LDAPError as e:
			self.logs.error({'message':'There was an error trying to bind meanwhile trying to do a search: %s' % e})

		return result

	def decode(self, word:bytes):
		return word.decode("utf-8")

	def findMatch(self, group:str, ADGroup:str):
		# Extract the Common Name from the string (letters, spaces and underscores)
		ADGroup = re.match('CN=((\w*\s?_?]*)*)', ADGroup).group(1)

		if not self.groupCaseSensitive:
			ADGroup = ADGroup.lower()

		# return match against supplied group/pattern (None if there is no match)
		try:
			return re.fullmatch(f'{group}.*', ADGroup).group(0)
		except:
			return None

	# Validate the groups in the Active Directory tree
	def validateGroups(self, groups):
		tree = self.getTree()

		# Crawl tree and extract the groups of the user
		userGroups = []
		for zone in tree:
			for element in zone:
				try:
					userGroups.extend(element['memberOf'])
				except TypeError:
					None
		userGroups = list(map(self.decode,userGroups))

		# List for the matches groups
		matchedGroups = []
		matchesByGroup = []
		for group in groups:
			# apply find match function to each value and then remove None values
			matches = list(filter(None,list(map(self.findMatch, repeat(group), userGroups))))
			if matches:
				matchesByGroup.append((group,matches))
				matchedGroups.extend(matches)

		self.logs.info({'message':'Validating groups.', 'username': self.username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})

		# Conditiona OR, true if just 1 group match
		if self.groupConditional == 'or':
			if matchedGroups:
				self.logs.info({'message':'At least one group is valid for the user.', 'username': self.username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
				return True,matchedGroups
		# Conditiona AND, true if all the groups match
		elif self.groupConditional == 'and':
			if len(groups) == len(matchesByGroup):
				self.logs.info({'message':'All groups are valid for the user.', 'username': self.username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
				return True,matchedGroups
		else:
			self.logs.error({'message':'Invalid group conditional.', 'username': self.username, 'conditional': self.groupConditional})
			return False,[]

		self.logs.error({'message':'Invalid groups for the user.', 'username': self.username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
		return False,[]
