import re, logging, sys
from flask import Flask
from flask import request
from flask import g
from flask_httpauth import HTTPBasicAuth
from aldap import Aldap
from cache import Cache
from os import environ
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from urllib.parse import unquote_plus

# --- Logging --------------------------------------------------------------------
loglevel_map = { 'DEBUG': logging.DEBUG,
				 'INFO': logging.INFO,
				 'WARN': logging.WARN,
				 'ERROR': logging.ERROR }

logformat_map = { 'JSON': "{'time':'%(asctime)s', 'name': '%(name)s', 'level': '%(levelname)s', 'message': '%(message)s'}",
				  'TEXT': "%(asctime)s - %(name)s - %(levelname)s - %(message)s" }

try:
	LOG_FORMAT = environ["LOG_FORMAT"]
except:
	LOG_FORMAT = 'TEXT'

try:
	LOG_LEVEL = environ["LOG_LEVEL"]
except:
	LOG_LEVEL = 'INFO'

logging.basicConfig(stream=sys.stdout, level=loglevel_map[LOG_LEVEL], format=logformat_map[LOG_FORMAT])
log = logging.getLogger('MAIN')			 

# --- Flask --------------------------------------------------------------------
app = Flask(__name__)
auth = HTTPBasicAuth()

# Cache
CACHE_EXPIRATION = 5 # Expiration in minutes
if "CACHE_EXPIRATION" in environ:
	CACHE_EXPIRATION = environ["CACHE_EXPIRATION"]
cache = Cache(CACHE_EXPIRATION)

@auth.verify_password
def login(username, password):
	log.debug(f"Received Headers: {str(request.headers.keys)}")

	# Either Client certificate is in the header (previously validated by nginx) or user and pass
	CLIENT_CERT = request.headers.get("x-forwarded-client-cert")
	if  CLIENT_CERT:
		username = getUserFromCertificate(CLIENT_CERT)
		password = None
	else:
		log.info("No client certificate provided in the header")
		if not username or not password:
			log.error("Username or password empty")
			return False

	try:
		# Get parameters from HTTP headers or from environment variables
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

		# Optional parameter
		LDAP_REQUIRED_GROUPS = ""
		if "Ldap-Required-Groups" in request.headers:
			LDAP_REQUIRED_GROUPS = request.headers["Ldap-Required-Groups"]
		elif "LDAP_REQUIRED_GROUPS" in environ:
			LDAP_REQUIRED_GROUPS = environ["LDAP_REQUIRED_GROUPS"]

		LDAP_REQUIRED_GROUPS_CONDITIONAL = "and" # The default is "and", another option is "or"
		if "Ldap-Required-Groups-Conditional" in request.headers:
			LDAP_REQUIRED_GROUPS_CONDITIONAL = request.headers["Ldap-Required-Groups-Conditional"]
		elif "LDAP_REQUIRED_GROUPS_CONDITIONAL" in environ:
			LDAP_REQUIRED_GROUPS_CONDITIONAL = environ["LDAP_REQUIRED_GROUPS_CONDITIONAL"]

		LDAP_SERVER_DOMAIN = ""
		if "Ldap-Server-Domain" in request.headers:
			LDAP_SERVER_DOMAIN = request.headers["Ldap-Server-Domain"]
		elif "LDAP_SERVER_DOMAIN" in environ:
			LDAP_SERVER_DOMAIN = environ["LDAP_SERVER_DOMAIN"]
	except KeyError as e:
		log.error(f"Invalid parameter: {e}")
		return False

	# Create the ALDAP object
	aldap = Aldap (
		LDAP_ENDPOINT,
		LDAP_MANAGER_DN_USERNAME,
		LDAP_MANAGER_PASSWORD,
		LDAP_SERVER_DOMAIN,
		LDAP_SEARCH_BASE,
		LDAP_SEARCH_FILTER
	)

	# Initialize the ALDAP object
	# The username and password are from the Basic Authentication pop-up form
	aldap.setUser(username, password)

	# Check groups only if they are defined
	matchesGroups = []
	if LDAP_REQUIRED_GROUPS:
		groups = LDAP_REQUIRED_GROUPS.split(",") # Split the groups by comma and trim
		groups = [x.strip() for x in groups] # Remove spaces
		validGroups, matchesGroups = aldap.validateGroups(groups, LDAP_REQUIRED_GROUPS_CONDITIONAL)
		if not validGroups:
			return False

	# Check authentication: 1st check client certificate, second cache, third authenticate in ldap
	if not CLIENT_CERT and not cache.validate(username, password) and not aldap.authenticateUser():
		return False

	# Include the user in the cache
	cache.add(username, password)

	# Success
	g.username = username # Set the username to send in the headers response
	g.matchesGroups = ','.join(matchesGroups) # Set the matches groups to send in the headers response
	return True


def getUserFromCertificate(CLIENT_CERT):
	log.debug(f'Received Certificate:', CLIENT_CERT)
	cert_str = unquote_plus(CLIENT_CERT)
	log.debug("Certificate Found")
	cert = x509.load_pem_x509_certificate(bytes(cert_str, 'utf-8'), default_backend())
	subject = str(cert.subject)
	log.debug(f'The issuer of the certificate is: {str(cert.issuer)}')
	log.debug(f'The subject of the certificate is: {str(cert.subject)}')

	p = re.compile("<Name\(CN=(.*)\)>")
	return p.search(subject).group(1)

# Catch-All URL
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth.login_required
def index(path):
	code = 200
	msg = "Another LDAP Auth"
	headers = [('x-username', g.username),('x-groups', g.matchesGroups)]
	return msg, code, headers

# Main
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=9000, debug=False)
