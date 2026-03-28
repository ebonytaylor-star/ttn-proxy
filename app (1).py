from flask import Flask, request, jsonify
import requests
import json
import os
import hashlib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

# Signup code — partners need this to register
# Change this anytime to stop new registrations
SIGNUP_CODE = "TTN2025"

# Simple file-based user store (persists on Render disk)
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    # Pre-load Ebony Taylor as first partner
    return {
        "ebonytaylor": {
            "name": "Ebony Taylor",
            "email": "Ebony.taylor100@gmail.com",
            "password": hash_password("TTN2025!"),
        }
    }

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/", methods=["GET"])
def home():
    return "TTN Proxy is running.", 200

@app.route("/api/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json()
        code = data.get("code", "").strip()
        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()

        if code != SIGNUP_CODE:
            return jsonify({"error": "Invalid signup code. Contact HR@thomastalentnetwork.com"}), 403

        if not all([username, password, name, email]):
            return jsonify({"error": "All fields are required."}), 400

        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters."}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400

        users = load_users()

        if username in users:
            return jsonify({"error": "Username already taken. Choose a different one."}), 409

        users[username] = {
            "name": name,
            "email": email,
            "password": hash_password(password),
        }
        save_users(users)

        return jsonify({"success": True, "name": name}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json()
        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()

        users = load_users()
        user = users.get(username)

        if not user or user["password"] != hash_password(password):
            return jsonify({"error": "Invalid username or password."}), 401

        return jsonify({
            "success": True,
            "name": user["name"],
            "email": user.get("email", "")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/claude", methods=["POST", "OPTIONS"])
def claude_proxy():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json()
        api_key = data.pop("__api_key", None)

        if not api_key:
            return jsonify({"error": {"message": "No API key provided"}}), 400

        response = requests.post(
            ANTHROPIC_API,
            json=data,
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": api_key,
            },
            timeout=60
        )

        return response.content, response.status_code, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
