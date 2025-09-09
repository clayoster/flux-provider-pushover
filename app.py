#!/usr/bin/env python

"""
This application acts as middleware to handle sending alerts from FluxCD to Pushover
"""

import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Load Pushover credentials from environment variables
PUSHOVER_USER_KEY = os.environ.get('PUSHOVER_USER_KEY', None)
PUSHOVER_API_TOKEN = os.environ.get('PUSHOVER_API_TOKEN', None)
# Set Authorization token to the same as PUSHOVER_API_TOKEN
EXPECTED_AUTH_TOKEN = PUSHOVER_API_TOKEN

# Pushover API
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

@app.route('/')
def bare_request():
    """ Bare Request Route """
    return 'Requests need to be made to /webhook', 400

@app.route('/health')
def healthcheck():
    """ Healthcheck Route """
    return "healthy"

@app.route("/webhook", methods=["POST"])
def webhook():
    """ The main route to the application """
    # Verify Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {EXPECTED_AUTH_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    # Parse JSON payload
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Extract fields from the FluxCD alert
    severity = data.get("severity", "INFO")
    message = data.get("message", "No Message")
    reason = data.get("reason", "Unknown")
    controller = data.get("reportingController", "Unknown")
    metadata = data.get("metadata", {})
    revision = metadata.get("revision", "Unknown")
    involved_object = data.get("involvedObject", {})
    kind = involved_object.get("kind", "Unknown")
    object_name = involved_object.get("name", "Unknown")

    # Build Pushover Message
    pushover_message = (
        f"{reason} [{severity.upper()}]\n"
        f"{message}\n\n"
        f"Controller: {controller}\n"
        f"Object: {kind.lower()}/{object_name}\n"
        f"Revision: {revision}\n"
    )

    # Send to Pushover
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

    # If sending to Pushover fails, return HTTP 500 and an error message.
    if response.status_code != 200:
        return jsonify({"error": "Failed to send to Pushover", "details": response.text}), 500

    # Otherwise, return HTTP 200 and "ok"
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
