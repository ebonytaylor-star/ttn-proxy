from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

@app.route("/", methods=["GET"])
def home():
    return "TTN Proxy is running.", 200

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
