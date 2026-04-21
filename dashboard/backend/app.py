from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from database import Database
import yaml
import os
import sys
from urllib.parse import urlparse

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "dashboard", "frontend")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "legacy_pi", "config.yaml")
DATABASE_PATH = os.path.join(BACKEND_DIR, "driver_data.db")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["SECRET_KEY"] = "driver_drowsiness_secret"
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db = Database(DATABASE_PATH)

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)


def get_camera_stream_info():
    def normalize_stream_url(url, default_path):
        if not isinstance(url, str):
            return None
        cleaned = url.strip()
        if not cleaned:
            return None

        if "://" not in cleaned:
            cleaned = f"http://{cleaned.lstrip('/')}"

        parsed = urlparse(cleaned)
        if parsed.scheme in {"http", "https"} and parsed.path in {"", "/"}:
            return cleaned.rstrip("/") + default_path
        return cleaned

    camera = config.get("camera", {})
    source = camera.get("source")

    if source == "esp32":
        url = normalize_stream_url(camera.get("esp32_url"), "/stream")
        if url:
            return {"enabled": True, "source": source, "url": url}
        return {
            "enabled": False,
            "source": source,
            "url": None,
            "message": "Set camera.esp32_url in pi/config.yaml.",
        }
    if source == "phone":
        url = normalize_stream_url(camera.get("phone_url"), "/video")
        if url:
            return {"enabled": True, "source": source, "url": url}
        return {
            "enabled": False,
            "source": source,
            "url": None,
            "message": "Set camera.phone_url in pi/config.yaml.",
        }

    return {
        "enabled": False,
        "source": source,
        "url": None,
        "message": "Dashboard preview supports network streams (esp32/phone) only.",
    }


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:asset_path>")
def frontend_assets(asset_path):
    return send_from_directory(FRONTEND_DIR, asset_path)


@app.route("/update", methods=["POST"])
def update_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

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


@app.route("/camera", methods=["GET"])
def get_camera():
    return jsonify(get_camera_stream_info())


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


def _start_mqtt_bridge():
    dash = config.get("dashboard", {})
    if not dash.get("use_mqtt"):
        return
    sys.path.insert(
        0, os.path.join(PROJECT_ROOT, "dashboard_backend")
    )
    try:
        from mqtt_listener import create_mqtt_listener
    except ImportError as e:
        print(f"[MQTT] paho-mqtt not installed, bridge disabled: {e}")
        return

    broker = dash.get("mqtt_broker", "localhost")
    port = int(dash.get("mqtt_port", 1883))
    topic = dash.get("mqtt_topic", "vehicle/driver/status")
    listener = create_mqtt_listener(broker, port, topic)

    def on_mqtt_message(data):
        db.insert_driver_data(data)
        socketio.emit("driver_update", data)

    listener.register_callback(on_mqtt_message)
    print(f"[MQTT] Bridge active: {broker}:{port} {topic}")


if __name__ == "__main__":
    host = config["dashboard"]["host"]
    port = config["dashboard"]["port"]
    debug = config["dashboard"]["debug"]
    _start_mqtt_bridge()
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
