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

# Check if dlib model exists
if [ ! -f "pi/shape_predictor_68_face_landmarks.dat" ]; then
    echo "Warning: dlib model not found!"
    echo "Run: wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    echo "     bzip2 -d shape_predictor_68_face_landmarks.dat.bz2"
fi

# Parse camera source from config
CAMERA_SOURCE=$(grep "source:" pi/config.yaml | head -1 | awk '{print $2}')

echo "Camera source: $CAMERA_SOURCE"
echo ""

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
echo "Dashboard: http://localhost:5000"
echo "=========================================="
echo "Press Ctrl+C to stop"

# Wait for any process to exit
wait $DASHBOARD_PID $DETECTOR_PID
