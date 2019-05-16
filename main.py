from flask import Flask
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def login(username, password):
    print(username)
    print(password)
    if username=="admin" and password=="demo123":
        return True
    return False

# Catch-All URL
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth.login_required
def index(path):
    code = 200
    msg = "Another LDAP Auth"
    return msg, code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
