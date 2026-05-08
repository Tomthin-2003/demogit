from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

TOKEN = os.environ.get("phone")

if not TOKEN:
    raise Exception("TOKEN not set!")

# device_id -> list of commands
command_queue = {}

# device_id -> latest location
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

    data = request.get_json() or {}
    cmd = data.get("command")
    device_id = data.get("device_id")

    if not cmd or not device_id:
        return error("missing command or device_id")

    command = {
        "id": int(time.time() * 1000),
        "command": cmd
    }

    if device_id not in command_queue:
        command_queue[device_id] = []

    command_queue[device_id].append(command)

    print(f"[QUEUE ADDED] {device_id} ->", command)

    return jsonify({"status": "added", "id": command["id"]})


# ----------------------------
# POLL COMMAND
# ----------------------------
@app.route("/poll", methods=["GET"])
def poll():
    if not auth(request):
        return error("unauthorized", 403)

    device_id = request.args.get("device_id")

    if not device_id:
        return error("missing device_id")

    if device_id in command_queue and command_queue[device_id]:
        cmd = command_queue[device_id].pop(0)

        print(f"[DISPATCH] {device_id} ->", cmd)

        # optional: cleanup empty queue
        if not command_queue[device_id]:
            del command_queue[device_id]

        return jsonify(cmd)

    return jsonify({"command": None})


# ----------------------------
# STATUS / LOCATION UPDATE
# ----------------------------
@app.route("/status", methods=["POST"])
def status():
    if not auth(request):
        return error("unauthorized", 403)

    data = request.get_json() or {}
    device_id = data.get("device_id")

    if not device_id:
        return error("missing device_id")

    print(f"[STATUS RECEIVED] {device_id} ->", data)

    if "lat" in data and "lon" in data:
        latest_location[device_id] = {
            "lat": data["lat"],
            "lon": data["lon"],
            "maps": data.get("maps"),
            "time": time.time()
        }

        print(f"[LOCATION UPDATED] {device_id} ->", latest_location[device_id])

    return jsonify({"ok": True})


# ----------------------------
# GET LOCATION
# ----------------------------
@app.route("/location", methods=["GET"])
def location():
    if not auth(request):
        return error("unauthorized", 403)

    device_id = request.args.get("device_id")

    if not device_id:
        return error("missing device_id")

    return jsonify(latest_location.get(device_id, {}))


# ----------------------------
# HOME
# ----------------------------
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "devices": list(command_queue.keys())
    })


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run()
