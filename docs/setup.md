# Driver Drowsiness Detection System - Setup Guide

## Overview

This project detects driver drowsiness using eye and mouth aspect ratios, then streams data to an IoT web dashboard. It supports multiple camera sources: Android phone via IP Webcam app, ESP32-CAM, USB webcam, or Raspberry Pi Camera Module.

---

## Hardware Requirements

| Component | Cost (₹) | Notes |
|-----------|----------|-------|
| Raspberry Pi 3/4 | 3000+ | Main processing unit |
| Camera source | 0-800 | Phone (free), ESP32-CAM (₹800), USB cam (₹500) |
| GPS Neo-6M | 400 | GPS module for location |
| Buzzer | 30 | 5V active buzzer |
| Vibration motor | 50 | Small DC motor |
| LED | 20 | Any color |
| Resistors | 20 | 330Ω for LED |
| Jumper wires | 50 | |
| **Total** | ~₹1300 | Excluding Pi |

---

## Hardware Connections

### GPIO Pin Layout (BCM numbering)

```
         +=========+
    3.3V | 1     2 | 5V
   GPIO2 | 3     4 | 5V
   GPIO3 | 5     6 | GND
   GPIO4 | 7     8 | GPIO14 (TX)
    GND  | 9    10 | GPIO15 (RX)
  GPIO17 | 11    12 | GPIO18
  GPIO27| 13    14 | GND
  GPIO22| 15    16 | GPIO23
    3.3V| 17    18 | GPIO24
  GPIO10| 19    20 | GND
   MOSI | 21    22 | GPIO25
   MISO | 23    24 | GPIO8
    CE0  | 25    26 | CE1
   GND  | 27    28 | SCL
  GPIO21| 29    30 | GND
  GPIO20| 31    32 | GPIO21
   GND  | 33    34 | GND
  GPIO19| 35    36 | GPIO16
  GPIO26| 37    38 | GPIO20
    GND  | 39    40 | GPIO21
         +=========+
```

### Connections

| Component | GPIO Pin | Notes |
|-----------|----------|-------|
| Buzzer positive | GPIO 17 | Pin 11 |
| Vibration motor | GPIO 27 | Pin 13 |
| LED (through 330Ω) | GPIO 22 | Pin 15 |
| GPS TX | GPIO 15 (RX) | Pin 10 |
| GPS RX | GPIO 14 (TX) | Pin 8 |
| GPS VCC | 5V | Pin 2 or 4 |
| GPS GND | GND | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

**Note:** GPS module needs serial interface enabled on Pi. Run `sudo raspi-config` → Interface Options → Serial → Disable login shell, Enable serial hardware.

---

## Software Setup

### 1. Raspberry Pi OS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y build-essential cmake git libopenblas-dev liblapack-dev

# Enable serial interface for GPS
# Run: sudo raspi-config
# Navigate: Interface Options → Serial → Disable login shell, Enable serial hardware
# Reboot after
```

### 2. Install Python Dependencies

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Pi dependencies
cd pi
pip install -r requirements.txt

# Install dashboard dependencies
cd ../dashboard/backend
pip install -r requirements.txt
```

### 3. Download dlib Landmark Model

```bash
# Download the facial landmark predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat pi/
```

---

## Camera Setup

### Option 1: Android Phone (Recommended)

1. Install **IP Webcam** app from Google Play Store
2. Connect phone to same WiFi as Pi
3. Open app → Scroll to bottom → Start server
4. Note the IP shown (e.g., `192.168.1.100`)
5. Update `config.yaml`:

```yaml
camera:
  source: "phone"
  phone_url: "http://192.168.1.100:8080/video"
```

### Option 2: ESP32-CAM

1. Install ESP32 board in Arduino IDE
2. Open `esp32/camera_webserver.ino`
3. Update WiFi credentials:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

4. Upload to ESP32-CAM (hold GPIO 0 + press EN to enter boot mode)
5. Note the IP shown in Serial Monitor
6. Update `config.yaml`:

```yaml
camera:
  source: "esp32"
  esp32_url: "http://192.168.1.XX/stream"
```

### Option 3: USB Webcam

1. Connect USB webcam to Pi
2. Update `config.yaml`:

```yaml
camera:
  source: "usb"
  usb_device: 0
```

### Option 4: Raspberry Pi Camera Module

1. Connect camera to Pi's CSI port
2. Enable camera: `sudo raspi-config` → Interface Options → Camera → Enable
3. Update `config.yaml`:

```yaml
camera:
  source: "picam"
  picam_index: 0
```

---

## Running the System

### Step 1: Start the Web Dashboard

```bash
cd /home/dev-lahrani/Desktop/EDU/IOT/CP/dashboard/backend
python3 app.py
```

Dashboard will be available at:
- **Local:** `http://127.0.0.1:5000`
- **Network:** `http://<pi-ip>:5000`

### Step 2: Start the Detection Program

```bash
cd /home/dev-lahrani/Desktop/EDU/IOT/CP/pi
python3 detector.py
```

### Step 3: Access the Dashboard

Open a browser on any device (phone, laptop, tablet) on the same network:

```
http://<raspberry-pi-ip>:5000
```

---

## Configuration

All settings are in `pi/config.yaml`:

```yaml
camera:
  source: "phone"          # phone | esp32 | usb | picam
  phone_url: "http://192.168.1.100:8080/video"

detection:
  ear_threshold: 0.22      # Eye closed if below this
  mar_threshold: 0.65      # Yawning if above this
  ear_consecutive_frames: 20
  mar_consecutive_frames: 15

hardware:
  buzzer_pin: 17
  vibration_pin: 27
  led_pin: 22
  buzzer_enabled: true
  vibration_enabled: true
  led_enabled: true

gps:
  port: "/dev/ttyAMA0"
  fallback_lat: 18.5204
  fallback_lon: 73.8567

dashboard:
  port: 5000
  push_interval: 2.0
```

---

## Testing

### Test Hardware Alerts

```bash
cd pi
python3 -c "
import yaml
from hardware import HardwareAlerts

with open('config.yaml') as f:
    config = yaml.safe_load(f)['hardware']

hw = HardwareAlerts(config)
hw.trigger('drowsy')
input('Press Enter to cleanup...')
hw.cleanup()
"
```

### Test Camera Stream

```bash
# Test if camera stream is accessible
curl -I "http://192.168.1.100:8080/video"
```

### Test GPS

```bash
# Check GPS serial connection
sudo minicom -D /dev/ttyAMA0 -b 9600
# Should see NMEA sentences like $GPGGA,...
```

---

## Troubleshooting

### Camera not connecting

- Verify phone/ESP32-CAM is on same WiFi network as Pi
- Check firewall: `sudo ufw allow 5000`
- Try accessing stream URL directly in browser

### dlib model not found

- Ensure `shape_predictor_68_face_landmarks.dat` is in `pi/` directory
- Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

### Face not detected

- Ensure good lighting
- Camera should be at eye level, 30-100cm from face
- Try lowering `ear_threshold` (e.g., 0.20)

### GPS not working

- Verify serial is enabled: `ls -l /dev/ttyAMA0`
- Check wiring: TX→RX, RX→TX
- Try `sudo chmod 666 /dev/ttyAMA0`

### Dashboard not loading

- Check Flask is running: `ps aux | grep python`
- Check port not used: `sudo netstat -tlnp | grep 5000`

---

## Project Structure

```
/home/dev-lahrani/Desktop/EDU/IOT/CP/
├── pi/
│   ├── config.yaml           # All configuration
│   ├── detector.py           # Main detection loop
│   ├── hardware.py           # Buzzer, vibration, LED
│   ├── gps.py                # GPS reader
│   ├── publisher.py          # Data to dashboard
│   └── requirements.txt
│
├── dashboard/
│   ├── backend/
│   │   ├── app.py            # Flask server
│   │   ├── database.py       # SQLite storage
│   │   └── requirements.txt
│   └── frontend/
│       ├── index.html        # Dashboard UI
│       ├── style.css
│       └── app.js
│
├── esp32/
│   └── camera_webserver.ino  # ESP32-CAM firmware
│
└── docs/
    └── setup.md              # This file
```

---

## Demonstration Flow

1. **Start dashboard** on Pi
2. **Start detector** on Pi
3. **Open dashboard** on laptop/phone
4. **Sit in front of camera** (phone or ESP32-CAM)
5. **Close eyes** for 2+ seconds
6. **Observe:**
   - Buzzer sounds
   - Vibration motor triggers
   - LED blinks
   - Dashboard updates to "DROWSY" status
   - Map shows location
   - Alert logged in history

---

## Optional: Remote Access

### Access from anywhere (not just local network)

Use **ngrok** for secure tunneling:

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.pub | sudo tee /usr/local/bin/ngrok
sudo chmod +x /usr/local/bin/ngrok

# Start dashboard then expose it
ngrok http 5000
```

Share the provided URL with judges/anyone.

---

## Cost Summary

| Item | Cost (₹) |
|------|----------|
| Raspberry Pi 3/4 | 3000 |
| Phone (already owned) | 0 |
| IP Webcam app | 0 |
| GPS Neo-6M | 400 |
| Buzzer | 30 |
| Vibration motor | 50 |
| LED + resistor | 40 |
| **Total** | ~₹3520 |

With ESP32-CAM instead of phone: add ~₹800
