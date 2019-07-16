from flask import Flask
from flask import request
from flask_httpauth import HTTPBasicAuth
from aldap import Aldap
from os import environ

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def login(username, password):

    if not username or not password:
        print("[ERROR] Username or password empty.")
        return False

    try:
        # Get parameters from Headers or from Environment variables
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

        # Optional parameter
        LDAP_SERVER_DOMAIN = ""
        if "Ldap-Server-Domain" in request.headers:
            LDAP_SERVER_DOMAIN = request.headers["Ldap-Server-Domain"]
        elif "LDAP_SERVER_DOMAIN" in environ:
            LDAP_SERVER_DOMAIN = environ["LDAP_SERVER_DOMAIN"]

    except KeyError as e:
        print("[ERROR] Invalid parameter: ", e)
        return False

    # Create the god of ldaps authentications object
    aldap = Aldap (
            LDAP_ENDPOINT,
            LDAP_MANAGER_DN_USERNAME,
            LDAP_MANAGER_PASSWORD,
            LDAP_SERVER_DOMAIN,
            LDAP_SEARCH_BASE,
            LDAP_SEARCH_FILTER,
            username,
            password
    )

    # Check for required groups only if the environment variable is defined
    if LDAP_REQUIRED_GROUPS:
        if not aldap.validateGroups( LDAP_REQUIRED_GROUPS.split(",") ):
            return False

    # Check if the username and password are valid
    if not aldap.authenticateUser():
        return False

    return True

# Catch-All URL
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth.login_required
def index(path):
    code = 200
    msg = "Another LDAP Auth"
    return msg, code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)
