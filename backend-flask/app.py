from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from jose import jwt, JWTError

from config import Config
from auth_service import authenticate_user, create_user_token

app = Flask(__name__)
app.config.from_object(Config)

# Allow your UI5 origin
CORS(app, origins=[
    "http://localhost:8080",  # UI5 dev server
])


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend running"})


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    token = create_user_token(user)
    return jsonify({"success": True, "token": token, "message": "Login successful"}), 200


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Not authenticated"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
            )
            username = payload.get("sub")
            if not username:
                raise JWTError("No subject in token")
        except JWTError:
            return jsonify({"detail": "Invalid or expired token"}), 401

        return f(username=username, *args, **kwargs)

    return decorated


@app.route("/auth/me", methods=["GET"])
@token_required
def who_am_i(username):
    return jsonify({"username": username})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)