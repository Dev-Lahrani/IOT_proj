from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
from database import Database
import threading
import time
import yaml
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder="../frontend", static_url_path="/static")
app.config["SECRET_KEY"] = "driver_drowsiness_secret"
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db = Database()

config_path = os.path.join(BASE_DIR, "pi", "config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


@app.route("/")
def index():
    return send_file(os.path.join(BASE_DIR, "dashboard", "frontend", "index.html"))


@app.route("/update", methods=["POST"])
def update_data():
    data = request.get_json()
    db.insert_driver_data(data)
    socketio.emit("driver_update", data)
    return jsonify({"success": True})


@app.route("/latest", methods=["GET"])
def get_latest():
    data = db.get_latest()
    return jsonify(data) if data else jsonify({"status": "NO_DATA"})


@app.route("/alerts", methods=["GET"])
def get_alerts():
    limit = request.args.get("limit", 50, type=int)
    alerts = db.get_alerts(limit)
    return jsonify(alerts)


@app.route("/stats", methods=["GET"])
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)


@app.route("/clear", methods=["POST"])
def clear_data():
    import sqlite3

    conn = sqlite3.connect(db.db_path)
    c = conn.cursor()
    c.execute("DELETE FROM driver_data")
    c.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def background_emitter():
    while True:
        socketio.sleep(2)


if __name__ == "__main__":
    socketio.start_background_task(target=background_emitter)
    host = config["dashboard"]["host"]
    port = config["dashboard"]["port"]
    debug = config["dashboard"]["debug"]
    socketio.run(app, host=host, port=port, debug=debug)
