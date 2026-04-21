# 🚗 Driver Drowsiness Detection System

An **ESP32-CAM-based** AI system that monitors driver fatigue in real-time and streams data to a web dashboard via MQTT.

## 🏗️ Architecture

```
ESP32-CAM (Detection Core) 
  ├─ Haar Cascade Face Detection
  ├─ Eye Aspect Ratio (EAR) / Mouth Aspect Ratio (MAR) Calculation
  ├─ Neo-6M GPS Module (UART)
  ├─ Hardware Alerts (Buzzer, LED, Vibration)
  └─ WiFi + MQTT Publisher
         ↓
   MQTT Broker (192.168.1.100:1883)
         ↓
   Dashboard Backend (Flask + Python)
         ↓
   Web Dashboard (Real-time WebSocket updates)
```

## ✨ Features

- **Real-time detection** using Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR)
- **Built-in ESP32-CAM** - No external camera setup needed
- **Hardware alerts**: Buzzer, vibration motor, and LED
- **GPS tracking**: Neo-6M module for location (UART)
- **IoT Dashboard**: Live status, map, alert history
- **MQTT Communication**: Lightweight, reliable IoT messaging
- **Low power consumption**: Optimized for embedded hardware

## 🚀 Quick Start

### 1. Flash ESP32-CAM Firmware
```bash
cd esp32/firmware

# Install platformio
pip install platformio

# Configure WiFi and MQTT in include/config.h
# Edit: WIFI_SSID, WIFI_PASSWORD, MQTT_BROKER

# Build and upload
platformio run -e esp32cam -t upload

# Monitor serial output
platformio device monitor -e esp32cam -b 115200
```

### 2. Start Dashboard Backend
```bash
# Install dependencies (if not already done)
pip install -r dashboard/backend/requirements.txt

# Run Flask app with MQTT listener
python dashboard_backend/mqtt_listener.py &
python dashboard/backend/app.py

# Open http://localhost:5000 in browser
```

## 🔧 Hardware Setup

### ESP32-CAM Connections
| Component | ESP32-CAM Pin | Notes |
|-----------|---------------|-------|
| Built-in Camera | Internal | OV2640 |
| Buzzer | GPIO 12 | Alert speaker |
| LED | GPIO 4 | On-board LED |
| Vibration Motor | GPIO 2 | Alert vibration |
| GPS RX | GPIO 16 | Neo-6M data |
| GPS TX | GPIO 17 | Neo-6M data |
| USB Power | 5V | Minimum 2A recommended |

### Wiring Diagram
```
ESP32-CAM
├─ GPIO 12 (Buzzer) → Transistor → Buzzer
├─ GPIO 4 (LED) → LED → GND
├─ GPIO 2 (Vibration) → Motor Driver → Motor
├─ GPIO 16 (GPS RX) → Neo-6M TX
├─ GPIO 17 (GPS TX) → Neo-6M RX
└─ 5V GND → Power Supply
```

## 📊 Configuration

All settings are in `esp32/firmware/include/config.h`:

```cpp
// WiFi
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"

// MQTT
#define MQTT_BROKER "192.168.1.100"
#define MQTT_PORT 1883

// Detection Thresholds
#define EAR_THRESHOLD 0.22f
#define MAR_THRESHOLD 0.65f
#define EAR_CONSECUTIVE_FRAMES 20
#define MAR_CONSECUTIVE_FRAMES 15
```

## 📡 MQTT Data Format

ESP32 publishes every 2 seconds to `vehicle/driver/status`:

```json
{
  "status": "NORMAL|DROWSY|YAWN|NO_FACE",
  "ear": 0.35,
  "mar": 0.40,
  "latitude": 18.5204,
  "longitude": 73.8567,
  "timestamp": 1713706858,
  "alert_triggered": false
}
```

## 📁 Project Structure

```
├── esp32/
│   ├── firmware/              ← ESP32-CAM C++ firmware
│   │   ├── src/              ← Source code
│   │   ├── include/          ← Headers
│   │   └── platformio.ini    ← Build config
│   └── README.md             ← Firmware docs
├── dashboard/
│   ├── backend/              ← Flask app
│   └── frontend/             ← Web UI
├── dashboard_backend/
│   └── mqtt_listener.py      ← MQTT bridge
├── legacy_pi/                ← Old Raspberry Pi code (archived)
└── docs/                     ← Setup guides
```

## 🔄 Data Flow

1. **ESP32 captures frame** from built-in camera
2. **Face detection** using Haar cascades
3. **Calculate EAR/MAR** from facial landmarks
4. **Compare thresholds** (drowsiness/yawning)
5. **Trigger alerts** if needed (buzzer, LED, vibration)
6. **Publish MQTT** message with detection data
7. **Dashboard receives** update via MQTT listener
8. **WebSocket update** sent to browser in real-time

## 📚 Documentation

- **ESP32 Firmware**: See `esp32/README.md`
- **Dashboard Backend**: See `dashboard/backend/README.md`
- **Setup Guide**: See `docs/setup.md`

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not working | Check GPIO pins, verify USB power (5V 2A+) |
| WiFi won't connect | Verify SSID/password, ensure 2.4GHz network |
| MQTT messages not received | Check broker IP, verify WiFi connection |
| GPS no signal | Move antenna outdoors, check UART pins |
| Low detection accuracy | Adjust EAR/MAR thresholds in config.h |

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

Pull requests welcome! See CONTRIBUTING.md for guidelines.
