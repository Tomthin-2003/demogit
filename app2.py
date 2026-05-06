from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

# 🔐 Token
TOKEN = os.environ.get("phone")

# 📦 In-memory storage
command_queue = []
latest_location = {}


# ----------------------------
# AUTH
# ----------------------------
def auth(req):
    return req.headers.get("Authorization") == TOKEN


def error(msg, code=400):
    return jsonify({"error": msg}), code


# ----------------------------
# SEND COMMAND
# ----------------------------
@app.route("/send", methods=["POST"])
def send():
    if not auth(request):
        return error("unauthorized", 403)

    data = request.json
    cmd = data.get("command")

    if not cmd:
        return error("missing command")

    # create structured command
    command = {
        "id": int(time.time()),   # unique id
        "command": cmd
    }

    command_queue.append(command)

    print("[QUEUE ADDED]", command)

    return jsonify({
        "status": "added",
        "id": command["id"]
    })


# ----------------------------
# POLL (PHONE)
# ----------------------------
@app.route("/poll", methods=["GET"])
def poll():
    if not auth(request):
        return error("unauthorized", 403)

    if command_queue:
        cmd = command_queue.pop(0)
        print("[DISPATCH]", cmd)
        return jsonify(cmd)

    return jsonify({"command": None})


# ----------------------------
# STATUS (FROM PHONE)
# ----------------------------
@app.route("/status", methods=["POST"])
def status():
    if not auth(request):
        return error("unauthorized", 403)

    global latest_location

    data = request.json
    print("[STATUS RECEIVED]", data)

    # Save GPS if present
    if "lat" in data and "lon" in data:
        latest_location = {
            "lat": data["lat"],
            "lon": data["lon"],
            "time": time.time()
        }

        print("[LOCATION UPDATED]", latest_location)

    return jsonify({"ok": True})


# ----------------------------
# GET LOCATION (LAPTOP)
# ----------------------------
@app.route("/location", methods=["GET"])
def location():
    if not auth(request):
        return error("unauthorized", 403)

    return jsonify(latest_location)


# ----------------------------
# ROOT (TEST)
# ----------------------------
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "queue_size": len(command_queue)
    })


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run()
