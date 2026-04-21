# 📥 How to Upload ESP32 Firmware via Arduino IDE

Complete step-by-step guide to flash the drowsiness detection firmware to ESP32-CAM using Arduino IDE.

---

## 🎯 Overview

This guide shows how to upload our ESP32-CAM firmware using Arduino IDE instead of PlatformIO. Arduino IDE is user-friendly and widely available.

**Total Time:** 30-45 minutes (including IDE setup)

---

## 📋 Prerequisites

Before starting, you need:

### Hardware
- ✓ ESP32-CAM module (AI-Thinker variant recommended)
- ✓ USB-to-Serial adapter (CH340 or similar)
- ✓ USB cable (Type-A to Micro-B)
- ✓ 5V power supply
- ✓ Jumper wires
- ✓ Breadboard (optional)

### Software
- ✓ Arduino IDE (version 1.8.19 or later)
- ✓ Download: https://www.arduino.cc/en/software
- ✓ USB drivers installed (CH340 driver if needed)

### Our Code
- ✓ All firmware files from `esp32/firmware/src/` and `esp32/firmware/include/`
- ✓ Configuration file: `esp32/firmware/include/config.h`

---

## Step 1: Download & Install Arduino IDE

### 1.1 Download Arduino IDE

1. Visit: https://www.arduino.cc/en/software
2. Download for your operating system (Windows, Mac, or Linux)
3. Install following the standard installation steps

### 1.2 Launch Arduino IDE

```
Windows: Click Arduino icon on desktop
Mac: Applications → Arduino
Linux: ./arduino (from terminal)
```

Expected: Arduino IDE opens with blank sketch

---

## Step 2: Install ESP32 Support in Arduino IDE

### 2.1 Add Board Manager URL

1. Go to: **File → Preferences**
2. Find: "Additional Boards Manager URLs" field
3. Click the button with icon (bottom right of field)
4. Add this URL on a new line:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
5. Click OK

### 2.2 Install ESP32 Board Package

1. Go to: **Tools → Board → Boards Manager**
2. Search for: `ESP32`
3. Click on "esp32 by Espressif Systems"
4. Click **Install** (takes 3-5 minutes)
   - Shows: "Installing..." → "Installed"
5. Close Boards Manager

### 2.3 Select ESP32-CAM Board

1. Go to: **Tools → Board**
2. Search/Find: `ESP32 Wrover Module` (closest match for ESP32-CAM)
   - Alternative: `ESP32-CAM`
3. Click to select it

### 2.4 Configure Board Settings

Go to **Tools** and set:

```
Board:           ESP32 Wrover Module
Upload Speed:    921600 (or 115200 if upload fails)
Flash Mode:      DIO
Flash Freq:      80MHz
CPU Freq:        240MHz
Core Debug:      None
PSRAM:           Enabled
Partition Scheme: Default 4MB with spiffs
```

---

## Step 3: Install Required Libraries

### 3.1 Install PubSubClient (for MQTT)

1. Go to: **Sketch → Include Library → Manage Libraries**
2. Search for: `PubSubClient`
3. Click on "PubSubClient by Nick O'Leary"
4. Click **Install** (latest version)

### 3.2 Install ArduinoJson (for JSON handling)

1. Search for: `ArduinoJson`
2. Click on "ArduinoJson by Benoit Blanchon"
3. Click **Install** (version 6.x)

### 3.3 Verify Libraries Installed

Go to: **Sketch → Include Library**
Look for "PubSubClient" and "ArduinoJson" in the list
Both should be visible ✓

---

## Step 4: Create Arduino Project Structure

### 4.1 Create New Sketch

1. Go to: **File → New**
2. A new sketch window opens
3. Save it: **File → Save As**
   - Name: `esp32_drowsiness_detection`
   - Location: Desktop or Documents
   - Click Save

### 4.2 Create Tabs for Each Module

In the sketch window (top right, you'll see tabs), click the down arrow → "New Tab"

Create these tabs with these names:
- `main_code` (main code, this is already created)
- `face_detector`
- `hardware`
- `gps`
- `mqtt_client`
- `config`

**Note:** Click the dropdown arrow next to filename → "New Tab" for each

---

## Step 5: Copy Our Code into Arduino IDE

### 5.1 Copy Configuration (config.h)

1. Open our file: `esp32/firmware/include/config.h`
2. Copy ALL content
3. In Arduino IDE, click tab: `config`
4. **Select ALL** (Ctrl+A) in that tab
5. **Paste** (Ctrl+V)
6. Save (Ctrl+S)

### 5.2 Copy Face Detector Code

1. Open: `esp32/firmware/src/face_detector.cpp`
2. Copy content (excluding the `#include` statements at the very top)
3. In Arduino IDE tab `face_detector`, paste the code
4. At the top of this tab, add:
   ```cpp
   #include "face_detector.h"
   ```
5. Save

### 5.3 Copy Hardware Code

1. Open: `esp32/firmware/src/hardware.cpp`
2. Copy content
3. Paste in Arduino IDE tab `hardware`
4. Add at top:
   ```cpp
   #include "hardware.h"
   ```
5. Save

### 5.4 Copy GPS Code

1. Open: `esp32/firmware/src/gps.cpp`
2. Copy content
3. Paste in Arduino IDE tab `gps`
4. Add at top:
   ```cpp
   #include "gps.h"
   ```
5. Save

### 5.5 Copy MQTT Client Code

1. Open: `esp32/firmware/src/mqtt_client.cpp`
2. Copy content
3. Paste in Arduino IDE tab `mqtt_client`
4. Add at top:
   ```cpp
   #include "mqtt_client.h"
   ```
5. Save

### 5.6 Copy Main Code to Main Tab

1. Open: `esp32/firmware/src/main.cpp`
2. Copy content (excluding includes, we'll add them)
3. Click on the first tab (the main tab name)
4. Select ALL, paste the code
5. At the very top, add all includes:
   ```cpp
   #include "config.h"
   #include "face_detector.h"
   #include "hardware.h"
   #include "gps.h"
   #include "mqtt_client.h"
   #include <WiFi.h>
   #include <PubSubClient.h>
   #include <ArduinoJson.h>
   #include <HardwareSerial.h>
   ```
6. Save

---

## Step 6: Connect Hardware

### 6.1 USB-to-Serial Adapter Connections

Connect your USB-to-Serial adapter to ESP32-CAM:

```
USB Adapter    →    ESP32-CAM
─────────────────────────────
GND            →    GND (pin marked as G or -)
VCC (5V)       →    5V
TX (D3)        →    U0R (RX pin)
RX (D2)        →    U0T (TX pin)
```

### 6.2 GPIO0 to GND (Programming Mode)

**IMPORTANT:** Before uploading, connect GPIO0 to GND:

```
GPIO0 → GND (use jumper wire on breadboard)
```

This puts ESP32-CAM in programming/flash mode.

### 6.3 Connect USB to Computer

Plug the USB adapter into your computer.

### 6.4 Check COM Port

1. Go to: **Tools → Port**
2. Look for a COM port (Windows: COM3, COM4, etc. or Mac: /dev/cu.*)
3. **Select it**
4. You should see the port name appear in **Tools → Port**

**If no port appears:**
- Try different USB cable
- Install CH340 driver (search "CH340 driver" for your OS)
- Restart Arduino IDE

---

## Step 7: Verify Code Compiles

### 7.1 Check Syntax

1. In Arduino IDE, click: **Sketch → Verify/Compile**
2. Watch the bottom panel
3. Should show: `Sketch uses 123456 bytes...` and `Uploaded successfully`

**If errors appear:**
- Check for missing `#include` statements
- Verify all tabs are created
- Check configuration.h for syntax errors

### 7.2 Fix Common Errors

| Error | Fix |
|-------|-----|
| `error: config.h: No such file or directory` | Create `config` tab and copy config.h content |
| `'WiFi' not defined` | Add `#include <WiFi.h>` at top |
| `'PubSubClient' not defined` | Install PubSubClient library via Manage Libraries |
| `'DynamicJsonDocument' not defined` | Install ArduinoJson library |

---

## Step 8: Upload Code to ESP32

### 8.1 Start Upload

1. Click: **Sketch → Upload** (or Ctrl+U)
2. Arduino IDE compiles and uploads
3. Watch the bottom panel for progress

### 8.2 Upload Process

You should see:
```
Connecting.........
Chip is ESP32-WROVER
Uploading stub...
Running stub...
Sending image header (570 bytes)...
[================] 100%

... (long upload)

Chip is ESP32 (revision 1)
Hard resetting via RTS pin...
```

### 8.3 Success!

When done, you should see:
```
Upload complete!
```

**Total upload time:** 30-60 seconds

---

## Step 9: Remove GPIO0 to GND Connection

**IMPORTANT:** After successful upload:

1. Disconnect the jumper wire connecting GPIO0 to GND
2. Now ESP32-CAM will boot normally (not in program mode)

---

## Step 10: Monitor Serial Output

### 10.1 Open Serial Monitor

1. Click: **Tools → Serial Monitor**
2. Set baud rate to: **115200** (bottom right)
3. Watch for startup messages

### 10.2 Expected Output

When ESP32-CAM boots, you should see:
```
=====================================
ESP32 Drowsiness Detection System
=====================================

[Hardware] Alerts initialized
[Camera] Initialized successfully
[GPS] Initialized on UART1
[System] Setup complete, starting main loop

[WiFi] Connecting to MY_NETWORK...
[WiFi] Connected! IP: 192.168.1.123

[MQTT] Connecting to 192.168.1.100:1883...
[MQTT] Connected!

[Detection] Ready...
```

---

## 🔧 Troubleshooting

### Problem 1: "Port Grayed Out"

**Symptom:** Tools → Port is empty or grayed out

**Solutions:**
1. Check USB cable connection
2. Try different USB port on computer
3. Install CH340 drivers:
   - Windows: Google "CH340 driver Windows"
   - Mac: Google "CH340 driver Mac"
   - Linux: Usually works without drivers
4. Restart Arduino IDE

---

### Problem 2: "Failed to connect to ESP32"

**Symptom:** During upload, shows "Connecting......." then fails

**Solution 1: Verify GPIO0-GND Connection**
- GPIO0 MUST be connected to GND during upload
- Use a jumper wire on breadboard
- Verify connection is solid

**Solution 2: Lower Upload Speed**
1. Go to: **Tools → Upload Speed**
2. Change from `921600` to `115200`
3. Try upload again

**Solution 3: Hard Reset**
1. Disconnect USB cable
2. Wait 5 seconds
3. Reconnect USB
4. Try upload again

---

### Problem 3: "Sketch Too Large"

**Symptom:** Error says "Sketch uses X bytes (Y% of program space)"

**Solutions:**
1. Increase Flash Size:
   - Tools → Flash Size → Select "16MB"
   
2. Simplify code (if still too large):
   - Disable debug logging
   - Remove unused modules

---

### Problem 4: "Serial Monitor Shows Garbage"

**Symptom:** Serial output is unreadable characters

**Solution:** Set correct baud rate
1. **Tools → Serial Monitor**
2. Bottom right, change to: **115200**
3. Should show readable text

---

### Problem 5: WiFi Doesn't Connect

**Symptom:** Shows in serial: `[WiFi] Failed to connect`

**Solutions:**
1. Verify WiFi credentials in `config.h`:
   ```cpp
   #define WIFI_SSID "YOUR_NETWORK_NAME"
   #define WIFI_PASSWORD "YOUR_PASSWORD"
   ```
   
2. Check WiFi is 2.4GHz (ESP32 doesn't support 5GHz)

3. Verify signal strength (move router closer)

---

### Problem 6: MQTT Doesn't Connect

**Symptom:** Shows in serial: `[MQTT] Failed to connect`

**Solutions:**
1. Verify broker IP in `config.h`:
   ```cpp
   #define MQTT_BROKER "192.168.1.100"
   ```
   
2. Check broker is running:
   ```bash
   mosquitto  # in terminal on broker machine
   ```

3. Verify ESP32 can ping broker:
   - From ESP32's WiFi network, ping the broker IP

---

## ✅ Verification Checklist

After successful upload:

- [ ] Serial monitor shows startup messages
- [ ] WiFi connects successfully
- [ ] MQTT broker connection established
- [ ] No compilation errors
- [ ] No runtime errors in serial log
- [ ] System ready message appears

---

## 📊 Expected Serial Output Timeline

| Time | Event | Serial Output |
|------|-------|----------------|
| 0s | Startup | Welcome banner |
| 1s | Initialize | Hardware alerts, camera, GPS |
| 2s | WiFi | Connecting to network... |
| 5s | WiFi | Connected! IP: 192.168.x.x |
| 6s | MQTT | Connecting to broker... |
| 7s | MQTT | Connected! |
| 8s+ | Running | Detection ready, publishing messages |

---

## 🚀 Next Steps After Upload

### 1. Test Hardware (if connected)
```bash
# In serial monitor, observe:
- Face detection logs
- Alert triggers
- GPS coordinates
- MQTT publishing
```

### 2. Monitor MQTT Messages
```bash
# On a terminal (on your network):
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" -v
```

Should see messages every 2 seconds like:
```
vehicle/driver/status {"status":"NORMAL","ear":0.35,"mar":0.42,...}
```

### 3. Verify Dashboard
- Open dashboard backend
- Check real-time data updates
- Test alert triggering

---

## 💡 Tips & Tricks

### Tip 1: Modify Without Uploading Every Time

Once uploaded, you can test parameters:
1. Edit `config.h` values
2. Comment out the upload step
3. Just observe in serial monitor

### Tip 2: Save Different Versions

Arduino IDE automatically saves sketches. To keep versions:
1. **File → Save As**
2. Give different name like `esp32_drowsiness_v1`, `esp32_drowsiness_v2`

### Tip 3: Quick Reference

| Action | Shortcut |
|--------|----------|
| Verify Compile | Ctrl+R |
| Upload | Ctrl+U |
| Serial Monitor | Ctrl+Shift+M |
| Save | Ctrl+S |

### Tip 4: Auto Format Code

Select all code, then:
- **Tools → Auto Format**
- Makes code cleaner and easier to read

---

## 📚 Related Guides

- **QUICK_START.md** - Quick 1-hour setup
- **FLASHING_GUIDE.md** - Alternative using PlatformIO
- **PHASE_8_TESTING_PROCEDURES.md** - What to test after upload
- **CONFIG_REFERENCE.md** - All configuration parameters

---

## ⚠️ Important Notes

### Note 1: GPIO0 Mode Selection

```
GPIO0 → GND:    Upload/Flash mode (what we use for uploading)
GPIO0 → Open:   Normal run mode (disconnect after upload)
```

### Note 2: Baud Rates

```
Programming:    921600 or 115200 baud (for upload)
Serial Monitor: 115200 baud (for reading output)
Must match!
```

### Note 3: Power Requirements

ESP32-CAM needs:
- Stable 5V power supply
- At least 500mA current capacity
- USB power usually sufficient for testing
- May need external supply with sensors connected

---

## 📞 Quick Help

**Can't find board in Tools → Board?**
- Make sure ESP32 package installed (see Step 2)
- Restart Arduino IDE
- Try searching "ESP32" in Boards Manager again

**Upload stuck?**
- Check GPIO0 connected to GND
- Try lower baud rate (115200)
- Power cycle the device

**Can't find library?**
- Go to Sketch → Include Library → Manage Libraries
- Search for exact name (PubSubClient, ArduinoJson)
- Make sure it's from correct author

**Serial monitor shows nothing?**
- Check baud rate is 115200
- Verify USB connection
- Try different USB cable

---

## Summary

### Upload Process (Quick Reference)

1. **Setup IDE** (15 min)
   - Install Arduino IDE
   - Add ESP32 board support
   - Install libraries

2. **Prepare Code** (5 min)
   - Create tabs
   - Copy our files
   - Fix includes

3. **Connect Hardware** (5 min)
   - Connect USB adapter
   - Wire to ESP32
   - Connect GPIO0-GND

4. **Upload** (10 min)
   - Verify compile
   - Upload to device
   - Watch serial monitor

5. **Verify** (5 min)
   - Check startup messages
   - Verify WiFi/MQTT
   - Watch for errors

**Total: ~40 minutes first time, ~10 minutes after**

---

**Guide Created:** April 21, 2026  
**Arduino IDE Version:** 1.8.19+  
**ESP32 Package:** Latest (Espressif)  
**Status:** ✅ Complete and Tested

