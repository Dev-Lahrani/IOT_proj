from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from database import Database
import yaml
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "dashboard", "frontend")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "pi", "config.yaml")
DATABASE_PATH = os.path.join(BACKEND_DIR, "driver_data.db")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["SECRET_KEY"] = "driver_drowsiness_secret"
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db = Database(DATABASE_PATH)

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:asset_path>")
def frontend_assets(asset_path):
    return send_from_directory(FRONTEND_DIR, asset_path)


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
if __name__ == "__main__":
    host = config["dashboard"]["host"]
    port = config["dashboard"]["port"]
    debug = config["dashboard"]["debug"]
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
