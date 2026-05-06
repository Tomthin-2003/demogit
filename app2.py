from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

TOKEN = os.environ.get("phone")

if not TOKEN:
    raise Exception("TOKEN not set!")

command_queue = []
latest_location = {}


def auth(req):
    return req.headers.get("Authorization") == TOKEN


def error(msg, code=400):
    return jsonify({"error": msg}), code


@app.route("/send", methods=["POST"])
def send():
    if not auth(request):
        return error("unauthorized", 403)

    data = request.get_json() or {}
    cmd = data.get("command")

    if not cmd:
        return error("missing command")

    command = {
        "id": int(time.time() * 1000),
        "command": cmd
    }

    command_queue.append(command)

    print("[QUEUE ADDED]", command)

    return jsonify({"status": "added", "id": command["id"]})


@app.route("/poll", methods=["GET"])
def poll():
    if not auth(request):
        return error("unauthorized", 403)

    if command_queue:
        cmd = command_queue.pop(0)
        print("[DISPATCH]", cmd)
        return jsonify(cmd)

    return jsonify({"command": None})


@app.route("/status", methods=["POST"])
def status():
    if not auth(request):
        return error("unauthorized", 403)

    global latest_location

    data = request.get_json() or {}
    print("[STATUS RECEIVED]", data)

    if "lat" in data and "lon" in data:
        latest_location = {
            "lat": data["lat"],
            "lon": data["lon"],
            "maps": data.get("maps"),   # 🔥 important
            "time": time.time()
        }

        print("[LOCATION UPDATED]", latest_location)

    return jsonify({"ok": True})


@app.route("/location", methods=["GET"])
def location():
    if not auth(request):
        return error("unauthorized", 403)

    return jsonify(latest_location)


@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "queue_size": len(command_queue)
    })


if __name__ == "__main__":
    app.run()
