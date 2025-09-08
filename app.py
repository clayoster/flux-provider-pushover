#!/usr/bin/env python

# Working curl command

import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Load Pushover credentials from environment variables
PUSHOVER_USER_KEY = os.environ.get('PUSHOVER_USER_KEY', None)
PUSHOVER_API_TOKEN = os.environ.get('PUSHOVER_API_TOKEN', None)
# EXPECTED_AUTH_TOKEN = os.getenv("WEBHOOK_AUTH_TOKEN", "mysecrettoken")
EXPECTED_AUTH_TOKEN = PUSHOVER_API_TOKEN

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

print(PUSHOVER_USER_KEY)
print(PUSHOVER_API_TOKEN)
print(EXPECTED_AUTH_TOKEN)

@app.route('/health')
def healthcheck():
    return "healthy"

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {EXPECTED_AUTH_TOKEN}":
        print(PUSHOVER_API_TOKEN)
        print(EXPECTED_AUTH_TOKEN)
        return jsonify({"error": "Unauthorized"}), 401

    # Parse JSON payload
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Extract fields from the FluxCD alert
    severity = data.get("severity", "info")
    message = data.get("message", "No message")
    reason = data.get("reason", "Unknown reason")
    metadata = data.get("metadata", {})
    summary = metadata.get("summary", "FluxCD Alert")
    revision = metadata.get("revision", "")

    # Build pushover message
    pushover_message = (
        f"[{severity.upper()}] {summary}\n"
        f"Reason: {reason}\n"
        f"Message: {message}\n"
        f"Revision: {revision}"
    )

    # Send to pushover
    response = requests.post(
        PUSHOVER_URL,
        data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": pushover_message,
            "title": "FluxCD"
        },
        timeout=(10, 10) # (connect timeout, read timeout) in seconds
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to send to Pushover", "details": response.text}), 500

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
