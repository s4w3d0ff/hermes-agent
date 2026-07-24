"""Magidex preprocessing tuner - Flask backend for scanner/preprocessing.py.

Usage: cd magidex/tuner && python server.py → http://127.0.0.1:8091/
Requires: flask, opencv-python (both in magidex venv).

Endpoints:
  POST /apply   - {"image": "data:image/jpeg;base64,...", "profile": {...}} → {"image": "data:image/png;base64,..."}
  GET  /profiles                     - list of profile names
  GET  /profile/<name>              - profile dict for given name

This server runs the ACTUAL scanner/preprocessing.py pipeline — results are
identical to running apply_profile() from Python, not an approximation.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory
from scanner.preprocessing import apply_profile, PROFILES as PY_PROFILES
import cv2  # noqa: F401
import numpy as np  # noqa: F401
import base64

app = Flask(__name__, static_folder=".")


@app.route("/profiles")
def get_profiles():
    return jsonify(list(PY_PROFILES.keys()))


@app.route("/profile/<name>")
def get_profile(name):
    if name not in PY_PROFILES:
        return jsonify({"error": "unknown profile"}), 404
    return jsonify(PY_PROFILES[name])


@app.route("/apply", methods=["POST"])
def apply():
    data = request.json
    image_bytes = data["image"]
    profile = data["profile"]

    # Decode base64 to numpy array @py:scanner/preprocessing.py:179
    img_data = base64.b64decode(image_bytes.split(",")[1])
    gray = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_GRAYSCALE)

    # Apply actual pipeline — mirrors scanner/preprocessing.py exactly @py:178-288
    result = apply_profile(gray, profile)

    # Return as base64 PNG for frontend display
    _, buf = cv2.imencode(".png", result)
    return jsonify({"image": "data:image/png;base64," + base64.b64encode(buf).decode()})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8091, debug=False)
