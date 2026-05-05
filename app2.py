from flask import Flask, request, jsonify
import os
app = Flask(__name__)
TOKEN = os.environ.get("phone") 
command_queue = []

def auth(req):
    return req.headers.get("Authorization") == TOKEN

@app.route("/send", methods=["POST"])
def send():
    if not auth(request):
        return jsonify({"error": "unauthorized"}), 403

    cmd = request.json.get("command")
    command_queue.append(cmd)
    return jsonify({"status": "added"})

@app.route("/poll", methods=["GET"])
def poll():
    if not auth(request):
        return jsonify({"error": "unauthorized"}), 403

    if command_queue:
        return jsonify({"command": command_queue.pop(0)})
    return jsonify({"command": None})

@app.route("/status", methods=["POST"])
def status():
    print(request.json)
    return jsonify({"ok": True})
