#!/bin/bash
# Start the full drowsiness detection system (host side).
# Prerequisites: mosquitto running, ESP32-CAM and ESP32 controller both powered on WiFi.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo " Driver Drowsiness Detection System"
echo "=========================================="

CONFIG="legacy_pi/config.yaml"
if [ ! -f "$CONFIG" ]; then
    echo "Error: $CONFIG not found"
    exit 1
fi

CAM_URL=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['camera']['esp32_url'])" 2>/dev/null)
echo "Camera stream : $CAM_URL"
echo "Dashboard     : http://$(hostname -I | awk '{print $1}'):5000"
echo ""

cleanup() {
    echo "Shutting down..."
    kill "$DASHBOARD_PID" "$DETECTOR_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# 1. Dashboard backend (Flask + MQTT bridge + WebSocket)
echo "[1/2] Starting dashboard..."
python3 dashboard/backend/app.py &
DASHBOARD_PID=$!
sleep 2

# 2. Detector (MediaPipe, pulls from camera URL, publishes to MQTT)
echo "[2/2] Starting detector..."
python3 dashboard_backend/detector.py &
DETECTOR_PID=$!

echo ""
echo "=========================================="
echo " System running — Ctrl+C to stop"
echo "=========================================="

wait "$DASHBOARD_PID" "$DETECTOR_PID"
