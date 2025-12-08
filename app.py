import os
import requests
from flask import Flask, request, jsonify, Response
from functools import wraps

app = Flask(__name__)

VALID_USERNAME = os.getenv('APP_USERNAME', 'admin')
VALID_PASSWORD = os.getenv('APP_PASSWORD', 'secret')
# ------------------------------------------------------

print(" * Starting proxy server...")
print(f" * Source URL: {os.getenv('SOURCE_URL')}")

if not os.getenv('SOURCE_URL') or not os.getenv('APP_USERNAME') or not os.getenv('APP_PASSWORD'):
    raise EnvironmentError("SOURCE_URL, APP_USERNAME, and APP_PASSWORD environment variables must be set.")


def authenticate():
    """Sends a 401 response that enables Basic Auth on the client side."""

    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    """Decorator to protect a Flask route with Basic Auth."""
    @wraps(f)
    def decorated(*args, **kwargs):

        auth = request.authorization

        if not auth or not (auth.username == VALID_USERNAME and auth.password == VALID_PASSWORD):
            return authenticate()

        return f(*args, **kwargs)
    return decorated


@app.route('/<path>')
@requires_auth
def protected_route(path):
    """
    This endpoint is protected and requires Basic Auth.
    If reached, the user is authenticated.
    """
    url = os.getenv('SOURCE_URL') + '/' + path
    app.logger.info(f"Fetching from: {url}")
    response = requests.get(url)
    try:
        response.raise_for_status()
        return Response(response.content)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch source", "details": str(e)}), 500


@app.route('/')
@requires_auth
def public_route():
    """A protected endpoint that requires authentication."""
    return "This is a protected page."


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
