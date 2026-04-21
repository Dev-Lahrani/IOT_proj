# ESP32-CAM Firmware Flashing Guide

This guide walks through building and uploading the drowsiness detection firmware to your ESP32-CAM module.

## Prerequisites

### Hardware
- **ESP32-CAM** (AI-Thinker module)
- **USB-to-Serial Adapter** (CH340, CP2102, or similar)
- **USB Cable** (USB-A to Micro-USB or USB-C depending on adapter)
- **Jumper Wires** (for connections)

### Software
- **Python 3.7+** installed
- **PlatformIO CLI** installed: `pip install platformio`
- **USB Driver** for your serial adapter (usually auto-installed)

## Hardware Setup

### 1. Connect ESP32-CAM to USB-Serial Adapter

| ESP32-CAM Pin | USB-Serial Pin |
|---------------|----------------|
| GND | GND |
| 5V | 5V |
| U0R (GPIO3) | TX |
| U0T (GPIO1) | RX |

**Note:** If powered via 5V on the module directly, ensure adequate power (2A+). Some setups require external 5V supply instead of USB.

### 2. Enter Programming Mode

To upload firmware, the ESP32-CAM must be in programming mode:

1. Connect **GPIO0 to GND** (holds it low)
2. Press **Reset Button** on module
3. Upload firmware (while GPIO0 is held to GND)
4. Disconnect GPIO0 from GND
5. Press **Reset Button** to boot into normal mode

Alternative: Some USB-to-Serial adapters have auto-reset circuits that handle this automatically with `DTR` and `RTS` pins.

## Configuration Before Flashing

Edit `esp32/firmware/include/config.h` to set your environment:

```cpp
// WiFi Configuration
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"

// MQTT Configuration
#define MQTT_BROKER "192.168.1.100"  // Your MQTT broker IP
#define MQTT_PORT 1883

// Detection Thresholds (adjust for accuracy)
#define EAR_THRESHOLD 0.22f
#define MAR_THRESHOLD 0.65f
#define EAR_CONSECUTIVE_FRAMES 20
#define MAR_CONSECUTIVE_FRAMES 15

// GPIO Pins (adjust if different hardware)
#define BUZZER_PIN 12
#define LED_PIN 4
#define VIBRATION_PIN 2
```

## Building the Firmware

### Step 1: Check your Serial Port

```bash
# Linux/macOS
ls /dev/tty.* /dev/ttyUSB* /dev/ttyACM*

# Windows
mode  # or use Device Manager
```

### Step 2: Update platformio.ini

Edit `esp32/firmware/platformio.ini` and set the correct serial port:

```ini
upload_port = /dev/ttyUSB0      # Linux
upload_port = /dev/cu.usbserial  # macOS
upload_port = COM3              # Windows
monitor_port = COM3             # Same port for serial monitoring
```

### Step 3: Build the Firmware

```bash
cd esp32/firmware
platformio run -e esp32cam
```

**Output should show:**
```
Building...
[✓] COMPILATION SUCCESSFUL
```

### Step 4: Upload to ESP32-CAM

**Important:** Hold GPIO0 to GND before uploading!

```bash
# With manual reset:
# 1. Connect GPIO0 to GND
# 2. Press Reset button
# 3. Run:
platformio run -e esp32cam -t upload

# If using auto-reset adapter, just run (no manual steps needed):
platformio run -e esp32cam -t upload
```

**Success output:**
```
Uploading .pio/build/esp32cam/firmware.bin
Uploading...
[✓] Firmware flashed successfully
Hard resetting via RTS pin...
```

## Verifying the Upload

### Monitor Serial Output

```bash
platformio device monitor -e esp32cam -b 115200
```

You should see:

```
=====================================
ESP32 Drowsiness Detection System
=====================================

[WiFi] Connecting to YOUR_SSID...
[WiFi] Connected! IP: 192.168.1.123
[MQTT] Connecting to 192.168.1.100:1883...
[MQTT] Connected!
[Camera] Initialized successfully
[Hardware] Alerts initialized
[GPS] Initialized on UART1
[System] Setup complete, starting main loop
```

### Check for Errors

| Error | Solution |
|-------|----------|
| `Failed to connect` | Check WiFi SSID/password in config.h |
| `No device found` | Check USB cable and serial adapter driver |
| `Permission denied` | Run with `sudo` or add user to `dialout` group: `sudo usermod -aG dialout $USER` |
| `Connection timeout` | Ensure GPIO0 is connected to GND during upload |

## MQTT Testing

Once the ESP32 is running and connected to MQTT:

### Subscribe to MQTT Topic

```bash
# Linux/macOS with mosquitto_sub:
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status"

# Or use mosquitto client if not installed:
pip install paho-mqtt
python3 -c "
import paho.mqtt.client as mqtt
def on_message(client, userdata, msg):
    print(f'{msg.topic}: {msg.payload.decode()}')
client = mqtt.Client()
client.on_message = on_message
client.connect('192.168.1.100', 1883, 60)
client.subscribe('vehicle/driver/status')
client.loop_forever()
"
```

You should see JSON messages every 2 seconds:

```json
{
  "status": "NORMAL",
  "ear": 0.35,
  "mar": 0.40,
  "latitude": 18.5204,
  "longitude": 73.8567,
  "timestamp": 1713706858,
  "alert_triggered": false
}
```

## Troubleshooting

### Camera Not Working
- Verify GPIO pins match your module (check AI-Thinker vs other variants)
- Check USB power supply (minimum 2A)
- Try with external 5V power supply

### WiFi Not Connecting
- Verify SSID and password in config.h
- Ensure network is 2.4GHz (ESP32 doesn't support 5GHz)
- Check router logs for connection attempts
- Try 802.11b mode: add to config.h: `#define WIFI_MODE WIFI_MODE_11B`

### MQTT Connection Failed
- Verify MQTT broker is running and accessible
- Check firewall rules (port 1883)
- Verify IP address is correct: `ping` the broker from ESP32's network
- Check MQTT broker logs for connection errors

### Serial Monitor Not Showing Output
- Check baud rate (must be 115200)
- Try different USB cable or adapter
- Hold Reset button while connecting serial monitor
- Add `delay(2000)` at start of `setup()` to allow time for serial connection

### Memory Issues / Crashes
- Reduce `FRAME_SKIP` to process fewer frames
- Reduce `EAR_CONSECUTIVE_FRAMES` and `MAR_CONSECUTIVE_FRAMES`
- Disable MQTT debug output
- Use PSRAM if available on your module

## Next Steps

1. **Verify detection accuracy** - Position camera and test EAR/MAR thresholds
2. **Calibrate hardware alerts** - Adjust buzzer pulses, LED blinks, vibration duration
3. **Test GPS** - Move outdoors with GPS antenna and check coordinates
4. **Start dashboard backend** - Run `python dashboard_backend/mqtt_listener.py`
5. **Monitor in dashboard** - Open web interface to see real-time updates

## Advanced: Debugging

### Enable Verbose Logging

Uncomment in firmware/src/main.cpp:

```cpp
#define DEBUG_MODE true
```

Recompile and upload. You'll see more detailed output on serial monitor.

### Check Memory Usage

In platformio.ini, add:

```ini
build_flags = -DDEBUG_VERBOSE
```

This will print heap usage and stack usage periodically.

### OTA (Over-The-Air) Updates

For future updates without serial connection:

1. Implement OTA in main.cpp (requires more memory)
2. Upload new firmware via WiFi from dashboard
3. See ESP-IDF OTA documentation for details

## Safety Notes

⚠️ **Important:**
- Never disconnect power while writing to flash
- Always use adequate power supply (minimum 2A @ 5V)
- GPIO0 must be HIGH during normal operation (don't leave connected to GND)
- Disconnect all external devices (buzzer, LED, motor) before flashing
- Allow time for serial monitor to initialize (device takes 2-3 seconds to boot)

## References

- [ESP-IDF Getting Started](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [ESP32-CAM AI-Thinker Pinout](https://github.com/espressif/esp32-camera)
- [MQTT Protocol](https://mqtt.org/)
