# ESP32-CAM Complete Pinout & Connections Reference

**Comprehensive guide to ALL ESP32-CAM pins and their connections in the drowsiness detection system**

---

## 📋 Quick Summary - All ESP32-CAM Pins

| Pin | Type | Function | Used For | Status |
|---|---|---|---|---|
| **GND** | Power | Ground | Power return | ✅ Required |
| **5V** | Power | +5V Power | Power input | ✅ Required |
| **3.3V** | Power | +3.3V Output | Camera power | ✅ Used |
| **U0T** | UART | TX (transmit) | Serial/USB TX | ✅ Required |
| **U0R** | UART | RX (receive) | Serial/USB RX | ✅ Required |
| **GPIO0** | Digital | Flash/Program | Upload firmware | ✅ Upload only |
| **GPIO2** | Output | Vibration motor | Haptic alert | ✅ Active |
| **GPIO4** | Output | LED indicator | Visual alert | ✅ Active |
| **GPIO12** | Output | Buzzer | Audio alert | ✅ Active |
| **GPIO16** | UART | GPS RX | GPS data in | ✅ Optional |
| **GPIO17** | UART | GPS TX | GPS data out | ✅ Optional |
| **RST** | Reset | System reset | Restart device | ✅ Available |
| **Camera pins** | Special | OV2640 camera | Image capture | ✅ Built-in |

---

## 🔌 SECTION 1: POWER CONNECTIONS (Always Connected)

### 5V Power Rail
```
USB-to-Serial Adapter
         │
         ├─→ 5V (red wire)
                  │
              (Breadboard)
                  │
         (power rail +)
          │      │      │
         5V     5V     5V
          │      │      │
    ┌─────┴──────┴──────┴─────┐
    │                         │
 [ESP32-CAM]            [GPS Module]
   5V pin                  (Vcc)
    │
   Powers entire module

Purpose: Main power supply for ESP32-CAM module
Voltage: 5V DC
Current: 0.5-1.2A (average operation)
```

### Ground Rail
```
USB-to-Serial Adapter
         │
         ├─→ GND (black wire)
                  │
              (Breadboard)
                  │
         (power rail -)
          │      │      │
         GND    GND    GND
          │      │      │
    ┌─────┴──────┴──────┴─────┐
    │                         │
 [ESP32-CAM]            [GPS Module]
   GND pin                 (GND)
    │
   Common return path

Purpose: Ground reference for all circuits
Voltage: 0V (reference)
Critical: Must have at least 1 GND connected, 2+ recommended for stability
```

### 3.3V Output (Optional, not powered by external source)
```
ESP32-CAM
  │
  ├─→ 3.3V pin (output)
        │
        └─→ Camera module (internal, already connected)

Note: 3.3V is OUTPUT from ESP32
Do NOT connect external 3.3V to this pin
```

---

## 🖲️ SECTION 2: SERIAL/UART CONNECTIONS (Required for Upload & Communication)

### Serial Upload (USB-to-Serial to ESP32)

**Connection Table:**
```
USB-to-Serial Adapter    →    ESP32-CAM
─────────────────────────────────────────
TX (green wire)          →    U0R (RX/receive)
RX (white wire)          →    U0T (TX/transmit)
```

**Detailed Explanation:**
```
USB Adapter TX (transmit data)
         │
         ├─→ GREEN WIRE
                │
           (Breadboard)
                │
         ESP32-CAM U0R
         (UART Receive)
         
         ⚡ Data flows: USB → ESP32


USB Adapter RX (receive data)
         ↑
         ├─← WHITE WIRE
                ↑
           (Breadboard)
                ↑
         ESP32-CAM U0T
         (UART Transmit)
         
         ⚡ Data flows: ESP32 → USB
```

**Why TX and RX are "Swapped":**
- Device A TX (transmit) connects to Device B RX (receive)
- Device B TX (transmit) connects to Device A RX (receive)
- This is correct! Never connect TX to TX or RX to RX

**Serial Parameters:**
- Baud Rate: 115200 bps
- Data Bits: 8
- Stop Bits: 1
- Parity: None
- Flow Control: None

**Used for:**
- Uploading firmware from Arduino IDE
- Serial debug messages during operation
- Monitoring system status

---

## ⚡ SECTION 3: GPIO OUTPUT PINS (Alert Outputs)

### GPIO12 - Buzzer (Audio Alert)
```
Configuration:
  Pin Number:    GPIO12
  Mode:          Digital Output
  Function:      Buzzer driver
  Voltage Level: 3.3V logic (enough for buzzer or relay)

Connection:
  ESP32-CAM GPIO12 → [300Ω resistor] → Buzzer → GND

Alert Pattern:
  Drowsiness: 3 pulses (beep-beep-beep)
  Yawn:       2 pulses (beep-beep)
  Each pulse: 500ms duration
  
Alert Code Location:
  File: esp32/firmware/src/hardware.cpp
  Function: triggerBuzzer()
  
Configuration:
  #define BUZZER_PIN 12                    (line 30 of config.h)
  #define BUZZER_DURATION_MS 500           (line 35 of config.h)
  #define BUZZER_ENABLED true              (line 41 of config.h)
  #define DROWSY_ALERT_COOLDOWN 10         (line 61 of config.h)
  #define YAWN_ALERT_COOLDOWN 15           (line 62 of config.h)
```

### GPIO4 - LED Indicator (Visual Alert)
```
Configuration:
  Pin Number:    GPIO4
  Mode:          Digital Output
  Function:      LED status indicator
  Voltage Level: 3.3V logic (can drive LED directly with resistor)

Connection:
  ESP32-CAM GPIO4 → [1kΩ resistor] → LED (+) → [LED (-)] → GND

Alert Pattern:
  Drowsiness: Blink 5 times (150ms on/off cycle)
  Yawn:       Blink 5 times (150ms on/off cycle)
  
Alert Code Location:
  File: esp32/firmware/src/hardware.cpp
  Function: triggerLED()
  
Configuration:
  #define LED_PIN 4                        (line 31 of config.h)
  #define LED_BLINK_DURATION_MS 150        (line 37 of config.h)
  #define LED_BLINK_COUNT 5                (line 38 of config.h)
  #define LED_ENABLED true                 (line 42 of config.h)
```

### GPIO2 - Vibration Motor (Haptic Alert)
```
Configuration:
  Pin Number:    GPIO2
  Mode:          Digital Output
  Function:      Vibration motor driver
  Voltage Level: 3.3V logic (may need relay/transistor for higher power)

Connection:
  ESP32-CAM GPIO2 → [Relay/Transistor] → Vibration Motor → GND

Alert Pattern:
  Drowsiness: Vibrate for 1 second
  Yawn:       Vibrate for 1 second
  Duration:   Continuous 1000ms

Alert Code Location:
  File: esp32/firmware/src/hardware.cpp
  Function: triggerVibration()
  
Configuration:
  #define VIBRATION_PIN 2                  (line 32 of config.h)
  #define VIBRATION_DURATION_MS 1000       (line 36 of config.h)
  #define VIBRATION_ENABLED true           (line 43 of config.h)
```

---

## 🛰️ SECTION 4: GPS CONNECTIONS (Optional, for Location)

### GPIO16 & GPIO17 - UART for GPS Module (Neo-6M)

**Connection to Neo-6M GPS Module:**
```
ESP32-CAM                    Neo-6M GPS Module
────────────────────────────────────────────────────
GPIO16 (UART RX)      ←      TX (GPS data out)
GPIO17 (UART TX)      →      RX (GPS data in)
5V                    →      Vcc (power)
GND                   →      GND (ground)
```

**GPS Configuration:**
```
UART Port:         Serial1
Baud Rate:         9600 bps
GPS Module:        Neo-6M (standard)
Update Interval:   1000ms (1 Hz)
Fallback Location: 18.5204°N, 73.8567°E (Pune, India)

Configuration in config.h:
  #define GPS_RX_PIN 16                    (line 46 of config.h)
  #define GPS_TX_PIN 17                    (line 47 of config.h)
  #define GPS_BAUD_RATE 9600               (line 48 of config.h)
  #define GPS_UPDATE_INTERVAL_MS 1000      (line 49 of config.h)
  #define FALLBACK_LATITUDE 18.5204f       (line 52 of config.h)
  #define FALLBACK_LONGITUDE 73.8567f      (line 53 of config.h)
```

**GPIO16 - GPS RX (Receive GPS Data)**
```
Neo-6M GPS Module
    │
    ├─→ TX pin (serial transmit)
            │
        Jumper wire
            │
    ESP32-CAM GPIO16
        (UART RX)
        
⚡ Data flow: GPS → ESP32-CAM
   GPS sends location, speed, altitude, time
```

**GPIO17 - GPS TX (Send Commands to GPS)**
```
ESP32-CAM GPIO17
    (UART TX)
        │
        ├─→ Jumper wire
            │
    Neo-6M GPS Module
        RX pin (serial receive)
        
⚡ Data flow: ESP32-CAM → GPS
   ESP32 sends configuration commands
```

**GPS Data Received:**
- Latitude & Longitude
- Altitude
- Speed
- Time & Date
- Satellite count
- Signal quality

---

## 📷 SECTION 5: CAMERA CONNECTIONS (Built-in OV2640)

### Camera Module (OV2640)
```
Location:        Top of ESP32-CAM module (already soldered)
Sensor:          OV2640 2MP camera
Connection Type: Parallel camera interface (internal CSI)
Power:           Powered from 3.3V rail

No additional connections needed - camera is built-in!

Configuration:
  #define CAMERA_WIDTH 320                 (line 56 of config.h)
  #define CAMERA_HEIGHT 240                (line 57 of config.h)
  #define CAMERA_JPEG_QUALITY 12           (line 58 of config.h)

Resolution:     320x240 (efficient for face detection)
Quality:        12/63 (medium quality, optimized for speed)
Frame Rate:     ~15-20 FPS (depends on detection processing)
Format:         JPEG (compressed for MQTT transmission)

Used for:
  - Real-time face detection
  - Drowsiness level estimation
  - Eye aspect ratio (EAR) calculation
  - Mouth aspect ratio (MAR) calculation
```

---

## 🔋 SECTION 6: SPECIAL PINS

### GPIO0 - Flash/Program Mode (Upload Only)
```
During Firmware Upload:
  GPIO0 → GND (CONNECTED)
  State:   Low (0V)
  Mode:    Bootloader/Programming mode
  
After Successful Upload:
  GPIO0 ✗ GND (DISCONNECTED)
  State:   Floating/High
  Mode:    Normal operation
  
Connection:
  ESP32-CAM GPIO0 → [Yellow jumper wire] → GND
  
⚠️ CRITICAL: Remove jumper after upload or device won't run app!
```

### RST - Reset Button Pin
```
Function:      System reset
Connection:    Optional button to GND
Purpose:       Force restart without power cycle
Pin Type:      Input (active low)

Optional Wiring:
  ESP32-CAM RST → [Push button] → GND
  
Usage:
  Press button: Device reboots immediately
  Useful for: Testing, troubleshooting, restarting app
```

---

## 📊 COMPLETE PIN LAYOUT

### Top View of ESP32-CAM
```
                    ┌────────────────────────────┐
                    │   📷 Camera Module (OV2640) │
                    └────────────────────────────┘
                                 │
                    ┌────────────────────────────┐
                    │      ESP32-CAM Pinout      │
                    └────────────────────────────┘

Top Row (Left to Right):
  [3.3V]  [GND]   [GPIO16]  [GPIO17]  [GND]
    │      │         │         │        │
   +3.3V  GND     GPS RX    GPS TX    GND
           
Bottom Row (Left to Right):
  [5V]   [Unpop]   [U0T]     [U0R]    [GND]
   │       ↓         │         │        │
  +5V   (empty)   TX out    RX in     GND
  
Left Side (Top to Bottom):
  [GPIO0]  ← Program mode (upload)
  [GPIO2]  ← Vibration motor
  [RST]    ← Reset button
  [GPIO4]  ← LED indicator
  [GPIO12] ← Buzzer
```

---

## 🎯 FUNCTIONAL PIN GROUPING

### Power Pins (3 pins)
```
┌─────────────────────┐
│   POWER GROUP       │
├─────────────────────┤
│ GND      - Ground   │
│ 5V       - Main     │
│ 3.3V     - Output   │
└─────────────────────┘
```

### Serial Communication (2 pins)
```
┌──────────────────────────┐
│   SERIAL/UART GROUP      │
├──────────────────────────┤
│ U0T - TX (ESP32 out)     │
│ U0R - RX (ESP32 in)      │
└──────────────────────────┘
Used for: Upload & debug
```

### Alert Outputs (3 pins)
```
┌──────────────────────────┐
│   ALERT OUTPUT GROUP     │
├──────────────────────────┤
│ GPIO12 - Buzzer (audio)  │
│ GPIO4  - LED (visual)    │
│ GPIO2  - Motor (haptic)  │
└──────────────────────────┘
Used for: Driver alerts
```

### GPS UART (2 pins)
```
┌──────────────────────────┐
│   GPS UART GROUP         │
├──────────────────────────┤
│ GPIO16 - GPS RX          │
│ GPIO17 - GPS TX          │
└──────────────────────────┘
Used for: Location data
```

### Control Pins (2 pins)
```
┌──────────────────────────┐
│   CONTROL GROUP          │
├──────────────────────────┤
│ GPIO0  - Program (upload)│
│ RST    - Reset button    │
└──────────────────────────┘
Used for: Upload & restart
```

---

## 🔧 WIRING SUMMARY TABLE

### All Connections Required

| From | To | Wire Color | Purpose | Status |
|---|---|---|---|---|
| USB GND | ESP32 GND | Black | Ground | ✅ Required |
| USB 5V | ESP32 5V | Red | Power | ✅ Required |
| USB TX | ESP32 U0R | Green | Serial RX | ✅ Required |
| USB RX | ESP32 U0T | White | Serial TX | ✅ Required |
| GPIO0 | GND | Yellow | Program mode | ✅ Upload only |
| GPIO12 | Buzzer | Orange | Audio alert | ✅ Active |
| GPIO4 | LED | Blue | Visual alert | ✅ Active |
| GPIO2 | Vibrator | Purple | Haptic alert | ✅ Active |
| GPIO16 | GPS TX | Brown | GPS data in | ⚠️ Optional |
| GPIO17 | GPS RX | Gray | GPS data out | ⚠️ Optional |
| 5V | GPS Vcc | Red | GPS power | ⚠️ Optional |
| GND | GPS GND | Black | GPS ground | ⚠️ Optional |

---

## 💾 FIRMWARE PIN MAPPING

**From esp32/firmware/include/config.h:**

```c
// Line 30-32: Output Pins for Alerts
#define BUZZER_PIN 12              // GPIO12 → Audio alert
#define LED_PIN 4                  // GPIO4 → Visual alert
#define VIBRATION_PIN 2            // GPIO2 → Haptic alert

// Line 46-47: GPS UART Pins
#define GPS_RX_PIN 16              // GPIO16 → Receive GPS data
#define GPS_TX_PIN 17              // GPIO17 → Send GPS commands

// Line 66: Serial Debug (UART0)
#define BAUD_RATE 115200           // U0T/U0R → Serial monitor

// Line 55-58: Camera Settings
#define CAMERA_WIDTH 320           // Image width (pixels)
#define CAMERA_HEIGHT 240          // Image height (pixels)
#define CAMERA_JPEG_QUALITY 12     // Quality (1-63)
```

---

## 📍 COMPLETE CONNECTION SEQUENCE

### Step-by-Step Wiring

**Step 1: Power Connections (Black & Red wires)**
```
USB Adapter GND (black) → Breadboard GND rail
USB Adapter 5V (red) → Breadboard 5V rail

Then:
Breadboard GND rail → ESP32-CAM GND pin
Breadboard 5V rail → ESP32-CAM 5V pin
```

**Step 2: Serial Connections (Green & White wires)**
```
USB Adapter TX (green) → Breadboard middle column
Breadboard → ESP32-CAM U0R (RX pin)

USB Adapter RX (white) → Breadboard middle column
Breadboard → ESP32-CAM U0T (TX pin)
```

**Step 3: GPIO0 for Upload (Yellow jumper, upload only!)**
```
ESP32-CAM GPIO0 → Yellow jumper → Breadboard GND rail
⚠️ REMOVE THIS JUMPER AFTER SUCCESSFUL UPLOAD
```

**Step 4: Alert Outputs (Orange, Blue, Purple)**
```
ESP32-CAM GPIO12 → Orange wire → Buzzer module → GND
ESP32-CAM GPIO4 → Blue wire → LED (with resistor) → GND
ESP32-CAM GPIO2 → Purple wire → Vibration motor → GND
```

**Step 5: GPS Connections (Brown & Gray, Optional)**
```
ESP32-CAM GPIO16 → Brown wire → Neo-6M GPS TX
ESP32-CAM GPIO17 → Gray wire → Neo-6M GPS RX
Breadboard 5V rail → Neo-6M GPS Vcc
Breadboard GND rail → Neo-6M GPS GND
```

---

## ✅ VERIFICATION CHECKLIST

### Before Upload
- [ ] GND connected (black wire)
- [ ] 5V connected (red wire)
- [ ] TX connected to U0R (green wire)
- [ ] RX connected to U0T (white wire)
- [ ] GPIO0 connected to GND (yellow jumper)
- [ ] All connections firm and not crossing
- [ ] COM port visible in Arduino IDE
- [ ] No short circuits

### After Upload
- [ ] Remove GPIO0→GND jumper
- [ ] Press RST button
- [ ] Serial Monitor shows startup messages
- [ ] Power/5V and serial wires still connected
- [ ] GPIO12 (buzzer) ready for testing
- [ ] GPIO4 (LED) ready for testing
- [ ] GPIO2 (vibration) ready for testing
- [ ] GPS (if connected) receiving satellites

---

## 🚨 COMMON MISTAKES

| Mistake | Problem | Solution |
|---|---|---|
| TX/RX Reversed | No serial communication | Swap green and white wires |
| GPIO0 Not Removed | Device stuck in bootloader | Remove GPIO0→GND jumper after upload |
| Wrong Baud Rate | Garbage in serial monitor | Set to 115200 in Arduino IDE |
| Missing GND | Intermittent failures | Add black wire from USB GND to ESP32 GND |
| 3.3V Instead of 5V | Unstable power, reset loops | Use red wire from USB 5V, not 3.3V |
| Loose Connections | Sporadic operation | Check all wires firmly in breadboard |
| Wrong Pin Numbers | Alerts don't work | Verify GPIO pins match config.h |

---

## 📚 REFERENCE FILES

- **esp32/firmware/include/config.h** - Pin configuration (42 parameters)
- **esp32/firmware/src/hardware.cpp** - Hardware alert functions
- **ARDUINO_IDE_UPLOAD_GUIDE.md** - Upload tutorial
- **WIRING_DIAGRAM_ASCII.txt** - Visual diagrams
- **ESP32_CAM_CONNECTIONS.md** - USB connections reference

---

## 💡 QUICK REFERENCE

**Total Pins Used: 11**
- Power: 3 (GND, 5V, 3.3V)
- Serial: 2 (U0T, U0R)
- Alerts: 3 (GPIO2, GPIO4, GPIO12)
- GPS: 2 (GPIO16, GPIO17)
- Program: 1 (GPIO0)

**Minimum Connections: 4 wires**
- Black (GND)
- Red (5V)
- Green (TX)
- White (RX)

**Total Connections with GPS: 6 more wires**
- Brown (GPIO16)
- Gray (GPIO17)
- Red (GPS 5V)
- Black (GPS GND)

---

**Last Updated:** April 21, 2026  
**Status:** ✅ Complete Reference  
**For:** ESP32-CAM Drowsiness Detection System
