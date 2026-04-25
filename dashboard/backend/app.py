from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from database import Database
import yaml
import os
import sys
from threading import Lock
from urllib.parse import urlparse

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "dashboard", "frontend")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "legacy_pi", "config.yaml")
DATABASE_PATH = os.path.join(BACKEND_DIR, "driver_data.db")
DEFAULT_STATUS_TOPIC = "vehicle/driver/status"
DEFAULT_GPS_TOPIC = "vehicle/gps"

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["SECRET_KEY"] = "driver_drowsiness_secret"
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db = Database(DATABASE_PATH)

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

latest_state_lock = Lock()
mqtt_listeners = []


def default_latest_state():
    return {
        "status": "NO_DATA",
        "ear": None,
        "mar": None,
        "lat": None,
        "lon": None,
        "latitude": None,
        "longitude": None,
        "timestamp": None,
    }


def normalize_payload(data):
    if not isinstance(data, dict):
        return None

    normalized = {key: value for key, value in data.items() if value is not None}
    status = normalized.get("status")
    has_status = isinstance(status, str) and bool(status.strip())
    if isinstance(status, str):
        cleaned = status.strip().upper()
        normalized["status"] = cleaned or "NO_DATA"

    lat = normalized.get("lat", normalized.get("latitude"))
    lon = normalized.get("lon", normalized.get("longitude"))
    if lat is not None:
        normalized["lat"] = lat
        normalized["latitude"] = lat
    if lon is not None:
        normalized["lon"] = lon
        normalized["longitude"] = lon

    if not has_status and "received_at" in normalized:
        normalized["timestamp"] = normalized["received_at"]
    elif "timestamp" not in normalized and "received_at" in normalized:
        normalized["timestamp"] = normalized["received_at"]

    return normalized


def load_latest_state():
    latest = db.get_latest()
    if not latest:
        return default_latest_state()

    normalized = normalize_payload(latest)
    if not normalized:
        return default_latest_state()

    state = default_latest_state()
    state.update(normalized)
    return state


latest_state = load_latest_state()


def get_latest_state():
    with latest_state_lock:
        return dict(latest_state)


def merge_latest_state(data):
    normalized = normalize_payload(data)
    if not normalized:
        return None

    with latest_state_lock:
        latest_state.update(normalized)
        latest_state.setdefault("status", "NO_DATA")
        if latest_state.get("lat") is not None:
            latest_state["latitude"] = latest_state["lat"]
        if latest_state.get("lon") is not None:
            latest_state["longitude"] = latest_state["lon"]
        return dict(latest_state)


def reset_latest_state():
    with latest_state_lock:
        latest_state.clear()
        latest_state.update(default_latest_state())
        return dict(latest_state)


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
            "message": "Set camera.esp32_url in legacy_pi/config.yaml.",
        }
    if source == "phone":
        url = normalize_stream_url(camera.get("phone_url"), "/video")
        if url:
            return {"enabled": True, "source": source, "url": url}
        return {
            "enabled": False,
            "source": source,
            "url": None,
            "message": "Set camera.phone_url in legacy_pi/config.yaml.",
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

    merged = merge_latest_state(data)
    if merged and data.get("status"):
        db.insert_driver_data(merged)
    if merged:
        socketio.emit("driver_update", merged)
    return jsonify({"success": True, "latest": merged})


@app.route("/latest", methods=["GET"])
def get_latest():
    return jsonify(get_latest_state())


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


@app.route("/health", methods=["GET"])
def get_health():
    dash = config.get("dashboard", {})
    return jsonify(
        {
            "ok": True,
            "camera": get_camera_stream_info(),
            "mqtt": {
                "enabled": bool(dash.get("use_mqtt")),
                "broker": dash.get("mqtt_broker", "localhost"),
                "port": int(dash.get("mqtt_port", 1883)),
                "status_topic": dash.get("mqtt_topic", DEFAULT_STATUS_TOPIC),
                "gps_topic": dash.get("mqtt_gps_topic", DEFAULT_GPS_TOPIC),
            },
            "latest": get_latest_state(),
            "stats": db.get_stats(),
        }
    )


@app.route("/clear", methods=["POST"])
def clear_data():
    db.clear_all()
    state = reset_latest_state()
    socketio.emit("driver_update", state)
    return jsonify({"success": True, "latest": state})


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
    status_topic = dash.get("mqtt_topic", DEFAULT_STATUS_TOPIC)
    gps_topic = dash.get("mqtt_gps_topic", DEFAULT_GPS_TOPIC)

    def on_status_message(data):
        merged = merge_latest_state(data)
        if not merged:
            return
        db.insert_driver_data(merged)
        socketio.emit("driver_update", merged)

    status_listener = create_mqtt_listener(broker, port, status_topic)
    status_listener.register_callback(on_status_message)
    mqtt_listeners.append(status_listener)
    print(f"[MQTT] Bridge active: {broker}:{port} {status_topic}")

    if gps_topic and gps_topic != status_topic:
        gps_listener = create_mqtt_listener(broker, port, gps_topic)

        def on_gps_message(data):
            merged = merge_latest_state(data)
            if merged:
                socketio.emit("driver_update", merged)

        gps_listener.register_callback(on_gps_message)
        mqtt_listeners.append(gps_listener)
        print(f"[MQTT] GPS bridge active: {broker}:{port} {gps_topic}")


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
