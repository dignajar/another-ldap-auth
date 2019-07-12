from flask import Flask
from flask_httpauth import HTTPBasicAuth
from aldap import Aldap
from os import environ

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def login(username, password):

    if not username or not password:
        print("Username or password empty.")
        return False

    aldap = Aldap (
            environ['LDAP_ENDPOINT'],
            environ['LDAP_MANAGER_DN_USERNAME'],
            environ['LDAP_MANAGER_PASSWORD'],
            environ['LDAP_SERVER_DOMAIN'],
            environ['LDAP_SEARCH_BASE'],
            environ['LDAP_SEARCH_FILTER'],
            username,
            password
    )

    # Check for required groups only if the environment variable is defined
    if environ['LDAP_REQUIRED_GROUPS']:
        requiredGroups = environ['LDAP_REQUIRED_GROUPS'].split(",")
        if not aldap.validateGroups(requiredGroups):
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
