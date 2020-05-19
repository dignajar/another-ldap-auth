import ldap
import time

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

	# Validate the groups in the Active Directory tree
	def validateGroups(self, groups, conditional):
		tree = self.search()

		print("[INFO][GROUPS] Validating the following groups:", groups)
		print("[INFO][GROUPS] Conditional:", conditional)

		# List for the matches groups
		matchesGroups = []
		for listAD in tree:
			for group in groups:
				# Check if the user has this group
				if group.lower() in str(listAD).lower():
					# The user has this group include the group in the matchesGroup
					matchesGroups.append(group)
					if conditional == 'or':
						print("[INFO][GROUPS] Matched group:",group)
						return True

		print("[INFO][GROUPS] Matched groups:",matchesGroups)

		# If the group is the same as matchesGroups means the user has all the groups
		if set(groups) == set(matchesGroups):
			print("[INFO][GROUPS] All groups are valid for the user.")
			return True

		print("[WARN][GROUPS] Invalid groups.")
		return False

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
