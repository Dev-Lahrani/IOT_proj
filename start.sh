#!/bin/bash
# Startup script - Run both dashboard and detector

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Driver Drowsiness Detection System"
echo "=========================================="

# Check if config exists
if [ ! -f "pi/config.yaml" ]; then
    echo "Error: config.yaml not found!"
    exit 1
fi

# Parse camera source from config
CAMERA_SOURCE=$(grep "source:" pi/config.yaml | head -1 | awk '{print $2}')
ESP32_STREAM=$(grep "esp32_url:" pi/config.yaml | head -1 | awk '{print $2}')

echo "Camera source: $CAMERA_SOURCE"
if [ "$CAMERA_SOURCE" = "\"esp32\"" ] || [ "$CAMERA_SOURCE" = "esp32" ]; then
    echo "ESP32 stream: $ESP32_STREAM"
fi
echo ""

PI_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$PI_IP" ]; then
    PI_IP="localhost"
fi

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $DASHBOARD_PID 2>/dev/null
    kill $DETECTOR_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start dashboard in background
echo "Starting dashboard on port 5000..."
cd dashboard/backend
python3 app.py &
DASHBOARD_PID=$!
cd ../..

sleep 2

# Start detector
echo "Starting detection..."
cd pi
python3 detector.py &
DETECTOR_PID=$!
cd ..

echo ""
echo "=========================================="
echo "System running!"
echo "Dashboard: http://$PI_IP:5000"
echo "=========================================="
echo "Press Ctrl+C to stop"

# Wait for any process to exit
wait $DASHBOARD_PID $DETECTOR_PID
