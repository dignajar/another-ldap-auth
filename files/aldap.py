import ldap
import time
import re
from itertools import repeat

class Aldap:
	def __init__(self, ldapEndpoint, dnUsername, dnPassword, serverDomain, searchBase, searchFilter):
		self.ldapEndpoint = ldapEndpoint
		self.searchBase = searchBase
		self.dnUsername = dnUsername
		self.dnPassword = dnPassword
		self.serverDomain = serverDomain
		self.searchFilter = searchFilter
		self.username = ''
		self.password = ''

		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		self.connect = ldap.initialize(self.ldapEndpoint)
		self.connect.set_option(ldap.OPT_REFERRALS, 0)
		self.connect.set_option(ldap.OPT_DEBUG_LEVEL, 255)

	def setUser(self, username, password):
		self.username = username
		self.password = password
		# Replace in the filter the variable "{username}" for the username
		self.searchFilter = self.searchFilter.replace("{username}", self.username)

	def search(self):
		print("[INFO][SEARCH] Searching by filter:", self.searchFilter)
		start = time.time()
		result = ""
		try:
			self.connect.simple_bind_s(self.dnUsername, self.dnPassword)
			result = self.connect.search_s(self.searchBase, ldap.SCOPE_SUBTREE, self.searchFilter)
			#self.connect.unbind_s()
		except ldap.LDAPError as e:
			print("[ERROR][SEARCH] There was an error when trying to bind.")
			print(e)

		print("[INFO][SEARCH] Time:", time.time()-start)
		return result

	def decode(self, word:bytes):
		return word.decode("utf-8")

	def findMatch(self, matchGroup:str, userGroup:str):
		# Extract the Common Name from the string (letters, spaces and underscores)
		userGroup = re.match('CN=((\w*\s?_?]*)*)', userGroup).group(1)

		# return match against supplied group/pattern (None if there is no match)
		try:
			return re.fullmatch(f'{matchGroup}.*', userGroup).group(0)
		except:
			return None

		def decode(self, word:bytes):
			return word.decode("utf-8")

	# Validate the groups in the Active Directory tree
	def validateGroups(self, groups, conditional):
		tree = self.search()

		# Crawl tree and extract the groups of the user
		userGroups = []
		for zone in tree:
			for element in zone:
				try: 
					userGroups.extend(element['memberOf'])
				except TypeError:
					None
		userGroups = list(map(self.decode,userGroups))

		print("[INFO][GROUPS] Validating the following groups:", groups)
		print("[INFO][GROUPS] Conditional:", conditional)

		# List for the matches groups
		matchesGroups = []
		for group in groups:
			# apply find match function to each value and then remove None values
			matches = list(filter(None,list(map(self.findMatch, repeat(group), userGroups))))
			matchesGroups.extend(matches)

		print("[INFO][GROUPS] Matched groups:",matchesGroups)

		# Conditiona OR, true if just 1 group match
		if conditional.lower() == 'or':
			for group in groups:
				if group in matchesGroups:
					print("[INFO][GROUPS] One of the groups is valid for the user.")
					return True,matchesGroups
		# Conditiona AND, true if all the groups match
		elif conditional.lower() == 'and':
			if set(groups) == set(matchesGroups):
				print("[INFO][GROUPS] All groups are valid for the user.")
				return True,matchesGroups
		else:
			print("[WARN][GROUPS] Invalid group conditional.")
			return False,[]

		print("[WARN][GROUPS] Invalid groups.")
		return False,[]

	def authenticateUser(self):
		finalUsername = self.username
		if self.serverDomain:
			# The configuration has serverDomain the username is username@domain
			finalUsername = self.username+"@"+self.serverDomain

		print("[INFO][AUTHENTICATION] Authenticating user:", finalUsername)

		start = time.time()
		try:
			self.connect.simple_bind_s(finalUsername, self.password)
			self.connect.unbind_s()
			print("[INFO][AUTHENTICATION] Username valid:", finalUsername)
			print("[INFO][AUTHENTICATION] Time:", time.time()-start)
			return True
		except ldap.INVALID_CREDENTIALS:
			print("[WARN][AUTHENTICATION] Invalid credentials.")
		except ldap.LDAPError as e:
			print("[ERROR][AUTHENTICATION] There was an error trying to bind.")
			print(e)

		return False
