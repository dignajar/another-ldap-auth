from flask import Flask
from flask import request
from flask import g
from flask_httpauth import HTTPBasicAuth
from os import environ
from aldap import Aldap
from cache import Cache
from logs import Logs

# --- Parameters --------------------------------------------------------------
# Enable or disable SSL self-signed certificate
LDAP_HTTPS_SUPPORT = False
if "LDAP_HTTPS_SUPPORT" in environ:
	LDAP_HTTPS_SUPPORT = (environ["LDAP_HTTPS_SUPPORT"] == "enabled")

# Key for encrypt the Session
FLASK_SECRET_KEY = "CHANGE_ME!"
if "FLASK_SECRET_KEY" in environ:
	FLASK_SECRET_KEY = str(environ["FLASK_SECRET_KEY"])

# Expiration in minutes
CACHE_EXPIRATION = 5
if "CACHE_EXPIRATION" in environ:
	CACHE_EXPIRATION = int(environ["CACHE_EXPIRATION"])

# --- Functions ---------------------------------------------------------------
def cleanMatchingUsers(item:str):
	item = item.strip()
	item = item.lower()
	return item

def cleanMatchingGroups(item:str):
	item = item.strip()
	return item

def setRegister(username:str, matchedGroups:list):
	g.username = username
	g.matchedGroups = ','.join(matchedGroups)

def getRegister(key):
	return g.get(key)

# --- Logging -----------------------------------------------------------------
logs = Logs('main')

# --- Cache -------------------------------------------------------------------
cache = Cache(CACHE_EXPIRATION)

# --- Flask -------------------------------------------------------------------
app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def login(username, password):
	if not username or not password:
		logs.error({'message': 'Username or password empty.'})
		return False

	try:
		if "Ldap-Endpoint" in request.headers:
			LDAP_ENDPOINT = request.headers.get("Ldap-Endpoint")
		else:
			LDAP_ENDPOINT = environ["LDAP_ENDPOINT"]

		if "Ldap-Manager-Dn-Username" in request.headers:
			LDAP_MANAGER_DN_USERNAME = request.headers["Ldap-Manager-Dn-Username"]
		else:
			LDAP_MANAGER_DN_USERNAME = environ["LDAP_MANAGER_DN_USERNAME"]

		if "Ldap-Manager-Password" in request.headers:
			LDAP_MANAGER_PASSWORD = request.headers["Ldap-Manager-Password"]
		else:
			LDAP_MANAGER_PASSWORD = environ["LDAP_MANAGER_PASSWORD"]

		if "Ldap-Search-Base" in request.headers:
			LDAP_SEARCH_BASE = request.headers["Ldap-Search-Base"]
		else:
			LDAP_SEARCH_BASE = environ["LDAP_SEARCH_BASE"]

		if "Ldap-Search-Filter" in request.headers:
			LDAP_SEARCH_FILTER = request.headers["Ldap-Search-Filter"]
		else:
			LDAP_SEARCH_FILTER = environ["LDAP_SEARCH_FILTER"]

		# List of groups separated by comma
		LDAP_MATCHING_GROUPS = ""
		if "Ldap-Matching-Groups" in request.headers:
			LDAP_MATCHING_GROUPS = request.headers["Ldap-Matching-Groups"]
		elif "LDAP_MATCHING_GROUPS" in environ:
			LDAP_MATCHING_GROUPS = environ["LDAP_MATCHING_GROUPS"]

		# The default is "and", another option is "or"
		LDAP_MATCHING_GROUPS_CONDITIONAL = "and"
		if "Ldap-Matching-Groups-Conditional" in request.headers:
			LDAP_MATCHING_GROUPS_CONDITIONAL = request.headers["Ldap-Matching-Groups-Conditional"]
		elif "LDAP_MATCHING_GROUPS_CONDITIONAL" in environ:
			LDAP_MATCHING_GROUPS_CONDITIONAL = environ["LDAP_MATCHING_GROUPS_CONDITIONAL"]

		# The default is "enabled", another option is "disabled"
		LDAP_MATCHING_GROUPS_CASE_SENSITIVE = True
		if "Ldap-Matching-Groups-Case-Sensitive" in request.headers:
			LDAP_MATCHING_GROUPS_CASE_SENSITIVE = (request.headers["Ldap-Matching-Groups-Case-Sensitive"] == "enabled")
		elif "LDAP_MATCHING_GROUPS_CASE_SENSITIVE" in environ:
			LDAP_MATCHING_GROUPS_CASE_SENSITIVE = (environ["LDAP_MATCHING_GROUPS_CASE_SENSITIVE"] == "enabled")

		# List of users separated by comma
		LDAP_MATCHING_USERS = ""
		if "Ldap-Matching-Users" in request.headers:
			LDAP_MATCHING_USERS = request.headers["Ldap-Matching-Users"]
		elif "LDAP_MATCHING_USERS" in environ:
			LDAP_MATCHING_USERS = environ["LDAP_MATCHING_USERS"]

		LDAP_SERVER_DOMAIN = ""
		if "Ldap-Server-Domain" in request.headers:
			LDAP_SERVER_DOMAIN = request.headers["Ldap-Server-Domain"]
		elif "LDAP_SERVER_DOMAIN" in environ:
			LDAP_SERVER_DOMAIN = environ["LDAP_SERVER_DOMAIN"]
	except KeyError as e:
		logs.error({'message': 'Invalid parameters.'})
		return False

	aldap = Aldap (
		LDAP_ENDPOINT,
		LDAP_MANAGER_DN_USERNAME,
		LDAP_MANAGER_PASSWORD,
		LDAP_SERVER_DOMAIN,
		LDAP_SEARCH_BASE,
		LDAP_SEARCH_FILTER,
		LDAP_MATCHING_GROUPS_CASE_SENSITIVE,
		LDAP_MATCHING_GROUPS_CONDITIONAL
	)

	cache.settings(
		LDAP_MATCHING_GROUPS_CASE_SENSITIVE,
		LDAP_MATCHING_GROUPS_CONDITIONAL
	)

	# Check if the username and password are valid
	# First check inside the cache and then in the LDAP server
	if not cache.validateUser(username, password):
		if aldap.authenticateUser(username, password):
			cache.addUser(username, password)
		else:
			return False

	# Validate user via matching users
	if LDAP_MATCHING_USERS:
		matchingUsers = LDAP_MATCHING_USERS.split(",") # Convert string to list
		matchingUsers = list(map(cleanMatchingUsers, matchingUsers))
		if username in matchingUsers:
			logs.info({'message':'Username inside the matching users list.', 'username': username, 'matchingUsers': ','.join(matchingUsers)})
			setRegister(username, [])
			return True

	# Validate user via matching groups
	matchedGroups = []
	if LDAP_MATCHING_GROUPS:
		matchingGroups = LDAP_MATCHING_GROUPS.split(",") # Convert string to list
		matchingGroups = list(map(cleanMatchingGroups, matchingGroups))
		validGroups, matchedGroups = cache.validateGroups(username, matchingGroups)
		if not validGroups:
			validGroups, matchedGroups = aldap.validateGroups(username, matchingGroups)
			if not validGroups:
				return False
			else:
				cache.addGroups(username, matchedGroups)

	# Success
	setRegister(username, matchedGroups)
	return True

# Catch-All URL
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth.login_required
def index(path):
	code = 200
	msg = "Another LDAP Auth"
	headers = [('x-username', getRegister('username')),('x-groups', getRegister('matchedGroups'))]
	return msg, code, headers

# Main
if __name__ == '__main__':
	app.secret_key = FLASK_SECRET_KEY
	if LDAP_HTTPS_SUPPORT:
		app.run(host='0.0.0.0', port=9000, debug=False, ssl_context='adhoc')
	else:
		app.run(host='0.0.0.0', port=9000, debug=False)
