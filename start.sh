#!/bin/bash
# Start the full drowsiness detection system (host side).
# Prerequisites: mosquitto running, ESP32-CAM and ESP32 controller both powered on WiFi.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="python3"

if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
fi

echo "=========================================="
echo " Driver Drowsiness Detection System"
echo "=========================================="

CONFIG="legacy_pi/config.yaml"
if [ ! -f "$CONFIG" ]; then
    echo "Error: $CONFIG not found"
    exit 1
fi

if ! "$PYTHON_BIN" -c "import flask, flask_socketio, yaml, paho.mqtt.client" >/dev/null 2>&1; then
    echo "Error: dashboard dependencies are missing for $PYTHON_BIN"
    echo "Install them with:"
    echo "  $PYTHON_BIN -m pip install -r dashboard/backend/requirements.txt"
    exit 1
fi

CAM_URL=$("$PYTHON_BIN" -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['camera']['esp32_url'])" 2>/dev/null)
DASHBOARD_PORT=$("$PYTHON_BIN" -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['dashboard']['port'])" 2>/dev/null)
echo "Camera stream : $CAM_URL"
echo "Dashboard     : http://$(hostname -I | awk '{print $1}'):${DASHBOARD_PORT:-5050}"
echo "Python        : $PYTHON_BIN"
echo ""

cleanup() {
    echo "Shutting down..."
    kill "$DASHBOARD_PID" 2>/dev/null
    if [ -n "${DETECTOR_PID:-}" ]; then
        kill "$DETECTOR_PID" 2>/dev/null
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# 1. Dashboard backend (Flask + MQTT bridge + WebSocket)
echo "[1/2] Starting dashboard..."
"$PYTHON_BIN" dashboard/backend/app.py &
DASHBOARD_PID=$!
sleep 2

# 2. Detector (MediaPipe, pulls from camera URL, publishes to MQTT)
if "$PYTHON_BIN" -c "import cv2, mediapipe, numpy" >/dev/null 2>&1; then
    echo "[2/2] Starting detector..."
    "$PYTHON_BIN" dashboard_backend/detector.py &
    DETECTOR_PID=$!
else
    echo "[2/2] Detector dependencies missing in $PYTHON_BIN"
    echo "      Dashboard is running, but live drowsiness detection is skipped."
fi

echo ""
echo "=========================================="
echo " System running — Ctrl+C to stop"
echo "=========================================="

if [ -n "${DETECTOR_PID:-}" ]; then
    wait "$DASHBOARD_PID" "$DETECTOR_PID"
else
    wait "$DASHBOARD_PID"
fi
