# ESP32-CAM Connections Reference

**Quick lookup guide for all ESP32-CAM pin connections**

---

## 🔌 USB-to-Serial Adapter → ESP32-CAM

### Power & Serial Connections (Always)

| USB Adapter Pin | ESP32-CAM Pin | Wire Color | Purpose |
|---|---|---|---|
| GND | GND | Black | Ground (power return) |
| 5V | 5V | Red | Power supply (+5V) |
| TX | U0R | Green | Serial TX → ESP32 RX |
| RX | U0T | White | Serial RX ← ESP32 TX |

### Programming Mode (Upload Only)

| Connection | GPIO0 Pin | Wire Color | Purpose | When |
|---|---|---|---|---|
| Connect | GPIO0 → GND | Yellow | Enable programming mode | **During upload ONLY** |
| Disconnect | GPIO0 ✗ GND | - | Run normal firmware | **After upload complete** |

---

## ⚠️ CRITICAL RULES

**❌ DO NOT IGNORE**

1. **GPIO0 to GND Connection**
   - ✅ MUST be connected during firmware upload
   - ❌ MUST be disconnected after upload completes
   - ⚠️ Forgetting step 2 causes device to not boot into app

2. **TX/RX Direction is Critical**
   - ✅ USB TX → ESP32 U0R (receive)
   - ✅ USB RX → ESP32 U0T (transmit)
   - ❌ Reversing these breaks all communication

3. **5V Power Required**
   - ✅ Use 5V from adapter (red wire)
   - ❌ Do NOT use 3.3V or other voltages
   - ⚠️ Insufficient power causes intermittent failures

4. **Ground Must Connect**
   - ✅ Always connect GND (black wire)
   - ❌ Missing ground causes weird behavior
   - ⚠️ Multiple grounds OK, at least one required

---

## 📍 Complete Pinout Reference

### Pin Locations on ESP32-CAM

**Top Row (Left to Right):**
```
[3.3V]  [GND]  [GPIO16]  [GPIO17]  [GND]
```

**Bottom Row (Left to Right):**
```
[5V]  [Unpopulated]  [U0T]  [U0R]  [GND]
```

**Left Side (Top to Bottom):**
```
GPIO0
GPIO2
RST
GPIO4
GPIO12
```

### All Pins with Functions

| Pin | Type | Function | Used In |
|---|---|---|---|
| **GND** | Power | Ground reference | Power/Serial/GPIO0 |
| **5V** | Power | Power input | Power supply |
| **3.3V** | Power | 3.3V output | Optional, don't use for input |
| **U0T** | Serial | TX (data out) | USB adapter RX |
| **U0R** | Serial | RX (data in) | USB adapter TX |
| **GPIO0** | Digital | Flash/Program mode | Connect to GND during upload |
| **GPIO2** | Output | Vibration motor | Alert vibration |
| **GPIO4** | Output | LED indicator | Alert light |
| **GPIO12** | Output | Buzzer | Alert sound |
| **GPIO16** | UART | GPS TX (optional) | Neo-6M GPS module |
| **GPIO17** | UART | GPS RX (optional) | Neo-6M GPS module |
| **RST** | Reset | Reset/Reboot | Manual reset button |

---

## 🔧 Step-by-Step Connection Process

### Before Upload (Programming Mode)

**Step 1: Gather Materials**
- [ ] USB-to-Serial adapter (CH340 or similar)
- [ ] ESP32-CAM module
- [ ] Breadboard (optional but recommended)
- [ ] 4 jumper wires (colors: black, red, green, white)
- [ ] 1 extra jumper wire (yellow) for GPIO0
- [ ] USB cable for adapter

**Step 2: Connect Power**
```
USB GND (black wire)  →  ESP32 GND
USB 5V (red wire)     →  ESP32 5V
```

**Step 3: Connect Serial/UART**
```
USB TX (green wire)   →  ESP32 U0R
USB RX (white wire)   →  ESP32 U0T
```

**Step 4: Enable Programming Mode**
```
GPIO0 (yellow wire)   →  GND
```
⚠️ **This enables firmware upload**

**Step 5: Plug In USB**
- Connect USB cable to adapter
- Connect adapter to computer
- Check if port appears in Arduino IDE

---

### After Successful Upload (Normal Mode)

**Step 1: Remove Programming Connection**
```
GPIO0 (yellow wire)   ✗ Disconnect from GND
```
✅ **Device will now boot into running firmware**

**Step 2: Keep Power & Serial Connected**
```
USB GND (black)  →  ESP32 GND  ← Keep connected
USB 5V (red)     →  ESP32 5V   ← Keep connected
USB TX (green)   →  ESP32 U0R  ← Keep connected
USB RX (white)   →  ESP32 U0T  ← Keep connected
```

**Step 3: Reset Device**
- Press RST button on ESP32-CAM
- Watch Serial Monitor for startup messages
- Verify WiFi and MQTT connection

---

## 🎯 Connection Verification Checklist

### Pre-Upload Checklist

- [ ] All 4 wires (black, red, green, white) connected
- [ ] GPIO0 to GND jumper installed
- [ ] USB cable connected to computer
- [ ] COM port visible in Arduino IDE Tools menu
- [ ] No wires crossing or touching
- [ ] All connections firm in breadboard

### Upload Success Indicators

- [ ] Arduino IDE shows "Upload complete"
- [ ] No error messages
- [ ] LEDs on adapter blink during upload
- [ ] Serial monitor shows upload messages

### Post-Upload Checklist

- [ ] GPIO0→GND jumper REMOVED
- [ ] Power (5V) and serial wires still connected
- [ ] Reset button pressed
- [ ] Serial Monitor shows startup: `Initializing...`
- [ ] WiFi connection message appears
- [ ] MQTT connection message appears

---

## 🚨 Troubleshooting by Symptom

### Upload Fails Immediately

**Most Common Cause:** GPIO0 not connected to GND
- ✅ **Solution:** Check GPIO0→GND jumper is firmly in place

**Other Causes:**
- COM port not selected in Arduino IDE → Tools → Port
- USB adapter driver not installed (CH340)
- USB cable is data cable (not charge-only)

### Serial Monitor Shows Garbage/Unreadable Text

**Cause:** Baud rate mismatch
- ✅ **Solution:** Set Serial Monitor to 115200 baud

**Also Check:**
- TX/RX not reversed
- Connections are firm

### Device Won't Boot After Upload

**Cause:** GPIO0 still connected to GND
- ✅ **Solution:** Remove GPIO0→GND jumper immediately after upload

### WiFi Connection Fails

**Causes:**
- SSID or password incorrect in config.h
- WiFi network not visible from device location
- WiFi module not powered enough

- ✅ **Solution:** Check config.h WiFi settings, recompile, re-upload

### MQTT Connection Fails

**Causes:**
- Broker IP address wrong in config.h
- Broker not running or not accessible
- Network connection established but MQTT broker unreachable

- ✅ **Solution:** Verify config.h broker IP, restart MQTT broker, check network

---

## 📊 Connection Summary Table

### All Connections at a Glance

```
┌─────────────────────────────────────────────────────────┐
│              USB Adapter → ESP32-CAM                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  POWER & SERIAL (Always Connected):                    │
│  ├─ GND (black)    → GND                              │
│  ├─ 5V (red)       → 5V                               │
│  ├─ TX (green)     → U0R (RX)                         │
│  └─ RX (white)     → U0T (TX)                         │
│                                                         │
│  PROGRAMMING (During Upload Only):                     │
│  └─ GPIO0          → GND (REMOVE after upload!)       │
│                                                         │
│  THEN AFTER UPLOAD:                                    │
│  └─ GPIO0 ✗ GND (disconnect, device boots)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🖼️ Visual Reference

### Upload Configuration

```
┌──────────────────┐              ┌──────────────────┐
│ USB-to-Serial    │              │   ESP32-CAM      │
│                  │              │                  │
│ [GND] ──────────→│→ black ──────→│ GND              │
│ [5V]  ──────────→│→ red ────────→│ 5V               │
│ [TX]  ──────────→│→ green ──────→│ U0R              │
│ [RX]  ←──────────│← white ←──────│ U0T              │
│                  │              │                  │
│                  │  yellow      │ GPIO0 ──→ GND    │
│                  │  (temp)      │ (program mode)   │
└──────────────────┘              └──────────────────┘
```

### Normal Operation (After Upload)

```
┌──────────────────┐              ┌──────────────────┐
│ USB-to-Serial    │              │   ESP32-CAM      │
│                  │              │                  │
│ [GND] ──────────→│→ black ──────→│ GND              │
│ [5V]  ──────────→│→ red ────────→│ 5V               │
│ [TX]  ──────────→│→ green ──────→│ U0R              │
│ [RX]  ←──────────│← white ←──────│ U0T              │
│                  │              │                  │
│                  │   (removed)  │ GPIO0 ✗ GND      │
│                  │              │ (app running)    │
└──────────────────┘              └──────────────────┘
```

---

## 📚 Related Documents

- **[ARDUINO_IDE_UPLOAD_GUIDE.md](ARDUINO_IDE_UPLOAD_GUIDE.md)** - Full upload tutorial
- **[WIRING_DIAGRAM_ASCII.txt](WIRING_DIAGRAM_ASCII.txt)** - Detailed wiring diagrams
- **[ARDUINO_IDE_QUICK_REFERENCE.txt](ARDUINO_IDE_QUICK_REFERENCE.txt)** - Quick reference card
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[esp32/firmware/include/config.h](esp32/firmware/include/config.h)** - Firmware configuration

---

## 💡 Pro Tips

1. **Use a breadboard** - Makes connections easier and more reliable
2. **Label your wires** - Prevents mistakes (GND=black, 5V=red, TX=green, RX=white)
3. **Check connections twice** - Most failures are reversed TX/RX or missing GND
4. **Keep GPIO0 jumper accessible** - You'll need to remove it after each upload
5. **Verify COM port** - Select correct port in Arduino IDE before uploading
6. **Set baud rate to 115200** - Always check Serial Monitor settings

---

## ❓ Quick Questions Answered

**Q: Can I use 3.3V instead of 5V?**
- No, always use 5V. ESP32-CAM requires 5V for stable operation.

**Q: What if I forget to disconnect GPIO0→GND after upload?**
- The device will stay in bootloader mode and won't run your app.
- Solution: Remove the jumper and press RST button.

**Q: Can I use jumpers other than what's shown?**
- Yes, as long as connections are correct: GND→GND, 5V→5V, TX↔RX swapped correctly.

**Q: Do I need all these connections?**
- Minimum: GND (2 wires) + 5V (1 wire) + TX (1 wire) + RX (1 wire) = 4 wires
- For upload: Add GPIO0→GND (5 wires total)

**Q: What if nothing shows in Serial Monitor?**
- Check: 1) COM port selected  2) Baud rate = 115200  3) USB cable connected  4) Correct cable (data, not charge)

---

**Last Updated:** April 21, 2026  
**Status:** ✅ Complete and Verified  
**Related:** Arduino IDE Upload Process
