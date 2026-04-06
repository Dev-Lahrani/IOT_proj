# 🚗 Driver Drowsiness Detection + IoT Dashboard

A Raspberry Pi-based AI system that monitors driver fatigue in real-time and streams data to a web dashboard.

## Features

- **Real-time detection** using Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR)
- **Multi-camera support**: Android phone (IP Webcam), ESP32-CAM, USB webcam, or Pi Camera
- **Hardware alerts**: Buzzer, vibration motor, and LED
- **GPS tracking**: Neo-6M module for location
- **IoT Dashboard**: Live status, map, and alert history
- **WebSocket**: Real-time updates without refreshing

## Quick Start

```bash
# 1. Install dependencies
pip install -r pi/requirements.txt
pip install -r dashboard/backend/requirements.txt

# 2. Download dlib model
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat pi/

# 3. Configure camera in pi/config.yaml

# 4. Run
bash start.sh

# 5. Open http://localhost:5000
```

## Camera Setup

### Android Phone (Recommended)
1. Install **IP Webcam** app
2. Start server, note the IP
3. Update `config.yaml`: `source: phone`, `phone_url: http://<ip>:8080/video`

### ESP32-CAM
1. Upload `esp32/camera_webserver.ino` to ESP32-CAM
2. Update WiFi credentials in the sketch
3. Update `config.yaml`: `source: esp32`, `esp32_url: http://<ip>/stream`

## Hardware

| Component | GPIO |
|-----------|------|
| Buzzer | 17 |
| Vibration | 27 |
| LED | 22 |
| GPS TX/RX | 15/14 |

## Files

```
pi/           - Detection code (detector.py, hardware.py, gps.py, publisher.py)
dashboard/    - Web dashboard (Flask backend + HTML/JS frontend)
esp32/        - ESP32-CAM firmware
docs/         - Setup guide
```

## Documentation

See `docs/setup.md` for detailed setup instructions.
