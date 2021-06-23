import ldap
import time
import re
from itertools import repeat
from logs import Logs

class Aldap:
	def __init__(self, ldapEndpoint, dnUsername, dnPassword, bindDN, searchBase, searchFilter, groupCaseSensitive, groupConditional):
		self.ldapEndpoint = ldapEndpoint
		self.searchBase = searchBase
		self.dnUsername = dnUsername
		self.dnPassword = dnPassword
		self.bindDN = bindDN
		self.searchFilter = searchFilter
		self.groupConditional = groupConditional.lower()
		self.groupCaseSensitive = groupCaseSensitive

		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		self.connect = ldap.initialize(self.ldapEndpoint)
		self.connect.set_option(ldap.OPT_REFERRALS, 0)
		self.connect.set_option(ldap.OPT_DEBUG_LEVEL, 255)

		self.logs = Logs(self.__class__.__name__)

	def authenticateUser(self, username:str, password:str) -> bool:
		'''
			Authenticate user by username and password
		'''
		finalUsername = username
		if self.bindDN:
			finalUsername = self.bindDN.replace("{username}", username)

		self.logs.info({'message':'Authenticating user.', 'username': username, 'finalUsername': finalUsername})

		start = time.time()
		try:
			self.connect.simple_bind_s(finalUsername, password)
			#self.connect.unbind_s()
			end = time.time()-start
			self.logs.info({'message':'Authentication successful.', 'username': username, 'elapsedTime': str(end)})
			return True
		except ldap.INVALID_CREDENTIALS:
			self.logs.warning({'message':'Invalid credentials.', 'username': username})
		except ldap.LDAPError as e:
			self.logs.error({'message':'There was an error trying to bind: %s' % e})

		return False

	def __getTree__(self, searchFilter:str) -> list:
		'''
			Returns the AD tree for the user, the user is search by the searchFilter
		'''
		result = []
		try:
			start = time.time()
			self.connect.simple_bind_s(self.dnUsername, self.dnPassword)
			result = self.connect.search_s(self.searchBase, ldap.SCOPE_SUBTREE, searchFilter)
			#self.connect.unbind_s()
			end = time.time()-start
			self.logs.info({'message':'Search by filter.', 'filter': searchFilter, 'elapsedTime': str(end)})
		except ldap.LDAPError as e:
			self.logs.error({'message':'There was an error trying to bind meanwhile trying to do a search: %s' % e})

		return result

	def __decode__(self, word:bytes) -> str:
		'''
			Convert binary to string. b'test' => 'test'
		'''
		return word.decode("utf-8")

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
		searchFilter = self.searchFilter.replace("{username}", username)
		tree = self.__getTree__(searchFilter)

		# Crawl tree and extract the groups of the user
		adGroups = []
		for zone in tree:
			for element in zone:
				try:
					adGroups.extend(element['memberOf'])
				except:
					None
		# Create a list from the elements and convert binary to str the items
		adGroups = list(map(self.__decode__,adGroups))

		self.logs.info({'message':'Validating groups.', 'username': username, 'groups': ','.join(groups), 'conditional': self.groupConditional})
		matchedGroups = []
		matchesByGroup = []
		for group in groups:
			matches = list(filter(None,list(map(self.__findMatch__, repeat(group), adGroups))))
			if matches:
				matchesByGroup.append((group,matches))
				matchedGroups.extend(matches)

		# Conditiona OR, true if just 1 group match
		if self.groupConditional == 'or':
			if len(matchedGroups) > 0:
				self.logs.info({'message':'At least one group is valid for the user.', 'username': username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
				return True,matchedGroups,adGroups
		# Conditiona AND, true if all the groups match
		elif self.groupConditional == 'and':
			if len(groups) == len(matchesByGroup):
				self.logs.info({'message':'All groups are valid for the user.', 'username': username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
				return True,matchedGroups,adGroups
		else:
			self.logs.error({'message':'Invalid conditional group.', 'username': username, 'conditional': self.groupConditional})
			return False,[],[]

		self.logs.error({'message':'Invalid groups for the user.', 'username': username, 'matchedGroups': ','.join(matchedGroups), 'groups': ','.join(groups), 'conditional': self.groupConditional})
		return False,[],[]
