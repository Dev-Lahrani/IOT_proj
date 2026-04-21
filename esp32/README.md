# ESP32-CAM Drowsiness Detection Firmware

## Overview
This is the main drowsiness detection firmware for the ESP32-CAM microcontroller. It handles:
- Real-time face detection using Haar cascades
- Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR) calculations
- Hardware alerts (buzzer, LED, vibration motor)
- GPS data collection from Neo-6M module
- MQTT publishing to remote dashboard backend

## Directory Structure
```
esp32/
├── firmware/
│   ├── src/
│   │   ├── main.cpp           # Main loop and system orchestration
│   │   ├── face_detector.cpp  # Face detection and aspect ratio calculations
│   │   ├── hardware.cpp       # GPIO control for alerts
│   │   ├── gps.cpp            # UART GPS reading (Neo-6M)
│   │   └── mqtt_client.cpp    # WiFi and MQTT publishing
│   ├── include/
│   │   ├── config.h           # All configuration constants
│   │   ├── face_detector.h
│   │   ├── hardware.h
│   │   ├── gps.h
│   │   └── mqtt_client.h
│   ├── data/
│   │   └── [Haar cascade XML files to be added]
│   └── platformio.ini         # PlatformIO configuration
└── README.md                  # This file
```

## Hardware Requirements
- **ESP32-CAM** (AI-Thinker module with OV2640 camera)
- **Neo-6M GPS Module** (UART: GPIO16 RX, GPIO17 TX)
- **Buzzer** (GPIO 12)
- **LED** (GPIO 4 - on-board LED)
- **Vibration Motor** (GPIO 2)
- **USB-to-Serial** for uploading firmware (CH340 or similar)

## Configuration
All configuration is in `firmware/include/config.h`:

### WiFi
```cpp
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"
```

### MQTT
```cpp
#define MQTT_BROKER "192.168.1.100"
#define MQTT_PORT 1883
#define MQTT_TOPIC "vehicle/driver/status"
```

### Detection Thresholds
```cpp
#define EAR_THRESHOLD 0.22f          // Eye Aspect Ratio threshold
#define MAR_THRESHOLD 0.65f          // Mouth Aspect Ratio threshold
#define EAR_CONSECUTIVE_FRAMES 20    // Frames before drowsiness alert
#define MAR_CONSECUTIVE_FRAMES 15    // Frames before yawn alert
```

### GPIO Pins
```cpp
#define BUZZER_PIN 12
#define LED_PIN 4
#define VIBRATION_PIN 2
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
```

## Building & Uploading

### Prerequisites
1. **PlatformIO** - Install via: `pip install platformio`
2. **ESP32 Board Support** - Auto-installed by PlatformIO
3. **Libraries** - Auto-installed from platformio.ini

### Build
```bash
cd esp32/firmware
platformio run -e esp32cam
```

### Upload
```bash
# Edit platformio.ini to set correct COM port
# Windows: COM3, Linux: /dev/ttyUSB0, macOS: /dev/cu.usbserial-*

platformio run -e esp32cam -t upload
```

### Monitor Serial Output
```bash
platformio device monitor -e esp32cam -b 115200
```

## MQTT Data Format
The ESP32 publishes detection data as JSON every 2 seconds:

```json
{
  "status": "NORMAL|DROWSY|YAWN|NO_FACE|ALERT",
  "ear": 0.35,
  "mar": 0.40,
  "latitude": 18.5204,
  "longitude": 73.8567,
  "timestamp": 1713706858,
  "alert_triggered": false
}
```

**Topics Published:**
- `vehicle/driver/status` - Detection results (every 2s)

## Detection Logic

### Drowsiness Detection (EAR)
1. Calculate Eye Aspect Ratio (EAR) from facial landmarks
2. If EAR < 0.22 for 20 consecutive frames → DROWSY
3. Trigger alert with 10s cooldown

### Yawning Detection (MAR)
1. Calculate Mouth Aspect Ratio (MAR) from facial landmarks
2. If MAR > 0.65 for 15 consecutive frames → YAWN
3. Trigger alert with 15s cooldown

### Alert Response
- Buzzer: 3 pulses for drowsy, 2 pulses for yawn
- LED: 5 blinks
- Vibration: 1 second continuous

## Troubleshooting

### Camera Not Working
- Check USB cable connection
- Verify GPIO pins match your ESP32-CAM board
- Try with external 5V power supply

### No GPS Signal
- Verify GPS module connections (RX/TX)
- Place antenna outdoors for better signal
- Check baud rate (9600)

### WiFi Connection Fails
- Verify SSID and password in config.h
- Check 2.4GHz WiFi network (ESP32 doesn't support 5GHz)
- Move closer to router

### MQTT Messages Not Publishing
- Verify MQTT broker is running
- Check broker IP and port in config.h
- Monitor dashboard backend logs

## Face Detection Notes
The current implementation uses Haar Cascade classifiers which are:
- **Lightweight** - Perfect for ESP32 memory constraints
- **Fast** - Processes frames at 5+ FPS
- **Proven** - Same algorithm used in Raspberry Pi version

For better accuracy with constrained hardware, consider:
- MediaPipe Lite (if ported to ESP32)
- Pre-trained TensorFlow Lite models
- MobileNet for face detection

## Performance Optimization
- **Frame Skip** - Processes every 2nd frame (configurable)
- **Grayscale Only** - Reduces memory and processing
- **QVGA Resolution** - 320x240 for speed
- **Fixed Memory Buffers** - No dynamic allocation in main loop

## Future Enhancements
- [ ] Integrate TensorFlow Lite for better accuracy
- [ ] Add SD card logging for offline backup
- [ ] Implement local model update via OTA
- [ ] Add accelerometer for vehicle motion detection
- [ ] WebSocket direct streaming (bypass dashboard)

## References
- [ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/)
- [PlatformIO Docs](https://docs.platformio.org/)
- [Eye Aspect Ratio Paper](https://vision.fe.uni-lj.si/cvww2016/proceedings/papers/04.pdf)
- [MQTT Protocol](https://mqtt.org/)
