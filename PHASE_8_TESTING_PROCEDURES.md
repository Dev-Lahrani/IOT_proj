# Phase 8: Comprehensive System Testing Guide

This document provides a practical step-by-step guide for executing the 70+ test cases to validate the entire system.

## Overview

**Testing Scope:** 7 phases covering hardware, software, integration, and system stability
**Total Duration:** 2-3 hours
**Required Environment:** ESP32-CAM, MQTT broker, dashboard backend, USB serial monitor

---

## Pre-Testing Setup (15 minutes)

### 1. Prepare Hardware
```bash
✓ ESP32-CAM assembled with all sensors connected
✓ USB-to-Serial adapter connected to computer
✓ Serial monitor ready (platformio device monitor)
✓ MQTT broker running on accessible IP
✓ Dashboard backend code ready to deploy
✓ Camera lens clean and positioned
```

### 2. Prepare Software
```bash
cd esp32/firmware

# Verify config.h is correct
cat include/config.h | grep WIFI_SSID
cat include/config.h | grep MQTT_BROKER

# Build firmware
platformio run -e esp32cam

# Prepare upload
# (Ensure GPIO0 to GND if manual reset needed)
```

### 3. Initialize MQTT Broker
```bash
# Terminal 1: Start MQTT broker
mosquitto

# Terminal 2: Monitor MQTT messages (leave running)
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" -v
```

---

## Phase 1: Firmware Upload & Connection (10 minutes)

### Test 1.1: Build Compilation
**Command:**
```bash
cd esp32/firmware
platformio run -e esp32cam
```

**Expected Output:**
```
[✓] COMPILATION SUCCESSFUL
```

**Success Criteria:**
- ✅ No compilation errors
- ✅ Binary generated
- ✅ Output shows "SUCCESSFUL"

**If Failed:**
- Check config.h syntax
- Verify all includes present
- Check for typos in source code

---

### Test 1.2: Firmware Upload
**Command:**
```bash
# Put ESP32 in programming mode (GPIO0 to GND)
platformio run -e esp32cam -t upload
```

**Expected Output:**
```
Uploading .pio/build/esp32cam/firmware.bin
Uploading.....
[✓] Firmware flashed successfully
Hard resetting via RTS pin...
```

**Success Criteria:**
- ✅ Upload completes without timeout
- ✅ Hard reset message appears
- ✅ Device reconnects after reset

**If Failed:**
- Check USB connection
- Verify GPIO0 held to GND during upload
- Try different baud rate (change in platformio.ini)

---

### Test 1.3: Serial Monitor Connection
**Command:**
```bash
platformio device monitor -e esp32cam -b 115200
# Press Reset button on ESP32
```

**Expected Output:**
```
=====================================
ESP32 Drowsiness Detection System
=====================================

[Hardware] Alerts initialized
[Camera] Initialized successfully
[GPS] Initialized on UART1
[System] Setup complete, starting main loop
```

**Success Criteria:**
- ✅ Startup messages appear within 2-3 seconds
- ✅ All initialization successful
- ✅ No garbage data or errors
- ✅ System ready messages shown

**Record:**
- Startup time: _____ seconds
- Any errors: _____

---

## Phase 2: Hardware I/O Testing (15 minutes)

### Test 2.1: GPIO Initialization Verification
**Steps:**
1. Watch serial output from startup
2. Note any GPIO error messages

**Expected in Logs:**
```
[Hardware] GPIO setup complete
[Hardware] Alerts initialized
```

**Success Criteria:**
- ✅ No GPIO initialization errors
- ✅ All 3 pins initialized (buzzer, LED, vibration)
- ✅ No permission denied errors

**Record:**
- GPIO status: ✓ All initialized / ✗ Errors

---

### Test 2.2: Manual Buzzer Test
**Hardware Setup:**
- Buzzer connected to GPIO 12 (with current limiting)
- GND connected to buzzer ground

**Steps:**
1. Modify config.h temporarily to enable buzzer test:
   ```cpp
   #define BUZZER_ENABLED true
   #define LED_ENABLED false
   #define VIBRATION_ENABLED false
   ```
2. Recompile and upload
3. Trigger alert by simulating drowsiness in code (or wait for real detection)

**Expected Behavior:**
- Drowsy alert: 3 beeps (500ms each with gap)
- Yawn alert: 2 beeps (500ms each with gap)

**Measurement:**
- [ ] Alert 1 - Drowsy: 3 beeps ✓
  - Pulse 1 duration: _____ ms
  - Pulse 2 duration: _____ ms
  - Pulse 3 duration: _____ ms

- [ ] Alert 2 - Yawn: 2 beeps ✓
  - Pulse 1 duration: _____ ms
  - Pulse 2 duration: _____ ms

**Success Criteria:**
- ✅ Correct number of pulses
- ✅ Duration ~500ms each
- ✅ Pulses separated by gaps
- ✅ No clipping or distortion

---

### Test 2.3: LED Blink Test
**Hardware Setup:**
- LED connected to GPIO 4 through resistor to GND

**Steps:**
1. Trigger alert (or simulate in code)
2. Observe LED behavior

**Expected:**
- LED blinks 5 times
- Each blink: ~150ms ON, ~150ms OFF

**Measurement:**
- [ ] Blink count: 5 ✓
- [ ] Blink 1: ON ___ms, OFF ___ms
- [ ] Total time: _____ seconds

**Success Criteria:**
- ✅ Exactly 5 blinks
- ✅ Consistent timing (~150ms each)
- ✅ No stuttering or incomplete cycles

---

### Test 2.4: Vibration Motor Test
**Hardware Setup:**
- Vibration motor connected to GPIO 2 via transistor/relay
- Proper power supply (may need dedicated 3-5V supply)

**Steps:**
1. Trigger alert
2. Feel or observe motor vibration

**Expected:**
- Motor vibrates when alert triggered
- Duration: ~1 second continuous

**Measurement:**
- [ ] Alert triggered
- [ ] Motor vibration detected: Yes / No
- [ ] Duration: _____ seconds
- [ ] Intensity: High / Medium / Low

**Success Criteria:**
- ✅ Motor activates when alert triggered
- ✅ Duration approximately 1 second
- ✅ No stuttering or incomplete cycles
- ✅ Adequate vibration intensity

---

## Phase 3: GPS Testing (20 minutes)

### Test 3.1: GPS UART Initialization
**Steps:**
1. Check serial output for GPS init message

**Expected:**
```
[GPS] Initialized on UART1
```

**Success Criteria:**
- ✅ Serial output shows initialization
- ✅ No UART errors

---

### Test 3.2: GPS Outdoor Signal (15 minutes)
**Setup:**
1. Move ESP32 outdoors with GPS antenna exposed
2. Clear view of sky (away from buildings/trees)
3. Wait 2-3 minutes for GPS lock

**Watch Serial Output:**
```
[GPS] Updated: 18.5204, 73.8567
[GPS] Updated: 18.5205, 73.8568
```

**Measurement:**
- [ ] GPS lock acquired: Yes / No
- [ ] Time to lock: _____ minutes
- [ ] Coordinates: _____ , _____
- [ ] Coordinate change observed: Yes / No

**Success Criteria:**
- ✅ Coordinates appear after 2-3 minutes
- ✅ Values are not 0.0, 0.0
- ✅ Slight changes show real data
- ✅ Format: Latitude between -90 to 90, Longitude between -180 to 180

**If GPS Not Locking:**
- [ ] Move antenna higher
- [ ] Ensure clear sky view
- [ ] Check RX/TX not swapped (GPIO 16/17)
- [ ] Verify power supply to GPS module (usually 5V)
- [ ] Wait additional 2-3 minutes

---

### Test 3.3: GPS Fallback (Indoors)
**Setup:**
1. Move ESP32 indoors (no GPS signal expected)
2. Watch serial output

**Expected:**
```
[GPS] Timeout, using fallback
[GPS] Updated: 18.5204, 73.8567 (fallback)
```

**Measurement:**
- [ ] Fallback coordinates used: Yes
- [ ] Coordinates match config.h: Yes / No
- [ ] System continues normally: Yes / No

**Success Criteria:**
- ✅ System doesn't hang when GPS unavailable
- ✅ Fallback coordinates appear
- ✅ Detection continues normally

---

## Phase 4: WiFi & MQTT Testing (20 minutes)

### Test 4.1: WiFi Connection
**Steps:**
1. Power up ESP32
2. Watch serial output

**Expected:**
```
[WiFi] Connecting to MY_NETWORK...
[WiFi] Connected! IP: 192.168.1.123
```

**Measurement:**
- [ ] WiFi connection time: _____ seconds
- [ ] IP address assigned: _____
- [ ] Network SSID correct: Yes / No

**Success Criteria:**
- ✅ Connects within 10 seconds
- ✅ Valid IP assigned (not 0.0.0.0)
- ✅ SSID matches config.h

---

### Test 4.2: MQTT Broker Connection
**Prerequisites:**
- MQTT broker running
- Network connectivity verified
- Broker IP correct in config.h

**Expected:**
```
[MQTT] Connecting to 192.168.1.100:1883...
[MQTT] Connected!
```

**Measurement:**
- [ ] Connection time: _____ seconds
- [ ] Broker IP visible in logs: Yes
- [ ] Port correct (1883): Yes / No

**Success Criteria:**
- ✅ Connects within 30 seconds
- ✅ No "Connection refused" errors
- ✅ "Connected!" message appears

---

### Test 4.3: MQTT Message Publishing
**Setup:**
1. ESP32 running and connected
2. Terminal monitoring MQTT topic:
   ```bash
   mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" -v
   ```

**Expected Output (every 2 seconds):**
```
vehicle/driver/status {"status":"NORMAL","ear":0.350,"mar":0.400,"latitude":18.5204,"longitude":73.8567,"timestamp":1234567890,"alert_triggered":false}
vehicle/driver/status {"status":"NORMAL","ear":0.340,"mar":0.405,"latitude":18.5204,"longitude":73.8567,"timestamp":1234567892,"alert_triggered":false}
```

**Measurement:**
- [ ] Messages arrive: Yes / No
- [ ] Frequency: Every _____ seconds
- [ ] JSON format valid: Yes / No
- [ ] Fields present: status, ear, mar, lat, lon, timestamp, alert_triggered

**Success Criteria:**
- ✅ Messages every ~2 seconds
- ✅ Valid JSON format
- ✅ All 7 required fields present
- ✅ No parse errors
- ✅ EAR/MAR values reasonable (0.0-1.0)

---

## Phase 5: Face Detection Testing (30 minutes)

### Test 5.1: Face Detection
**Setup:**
1. Position camera at typical driving position
2. Show face to camera
3. Watch logs

**Expected:**
```
[Detection] Face detected!
```

**Measurement:**
- [ ] Face detected on attempt: Yes / No
- [ ] Detection immediate: Yes / No
- [ ] No false positives: Yes / No

**Success Criteria:**
- ✅ Face detected with person looking at camera
- ✅ No significant delay (<1 second)
- ✅ No false positives when showing objects

---

### Test 5.2: Eyes Closed (Drowsiness)
**Sequence:**
1. Face camera normally (baseline)
   - Observe EAR value: _____
   - Expected: ~0.35-0.40
2. Close both eyes and hold for 5+ seconds
   - Observe EAR value: _____
   - Expected: ~0.10-0.20
   - Expected: Buzzer beeps after ~4 seconds (20 frames at 5 FPS)
3. Open eyes
   - Expected: Buzzer stops, EAR returns to high value

**Measurements:**
- [ ] Test 1 - Eyes Open
  - EAR value: _____
  - Status in MQTT: _____
  
- [ ] Test 2 - Eyes Closed
  - EAR value: _____
  - Alert triggered: Yes / No
  - Time to alert: _____ seconds
  - Status in MQTT: _____
  - Buzzer pulses: 3 / 2 / other
  
- [ ] Test 3 - Eyes Open Again
  - EAR value: _____
  - Alert stopped: Yes / No

**Success Criteria:**
- ✅ EAR ~0.35-0.40 with eyes open
- ✅ EAR ~0.10-0.20 with eyes closed
- ✅ Alert after EAR_CONSECUTIVE_FRAMES threshold
- ✅ Correct pulse count (3 for drowsy)

---

### Test 5.3: Yawning Detection
**Sequence:**
1. Mouth closed (baseline)
   - Observe MAR value: _____
   - Expected: ~0.30-0.40
2. Open mouth wide (yawn) and hold for 3+ seconds
   - Observe MAR value: _____
   - Expected: ~0.65-0.80
   - Expected: Buzzer beeps after ~3 seconds (15 frames at 5 FPS)
3. Close mouth
   - Expected: Buzzer stops, MAR returns to low value

**Measurements:**
- [ ] Test 1 - Mouth Closed
  - MAR value: _____
  - Status in MQTT: _____
  
- [ ] Test 2 - Mouth Wide Open
  - MAR value: _____
  - Alert triggered: Yes / No
  - Time to alert: _____ seconds
  - Status in MQTT: _____
  - Buzzer pulses: 2 / 3 / other
  
- [ ] Test 3 - Mouth Closed Again
  - MAR value: _____
  - Alert stopped: Yes / No

**Success Criteria:**
- ✅ MAR ~0.30-0.40 with mouth closed
- ✅ MAR ~0.65-0.80 with mouth open
- ✅ Alert after MAR_CONSECUTIVE_FRAMES threshold
- ✅ Correct pulse count (2 for yawn)

---

### Test 5.4: Alert Cooldown
**Sequence:**
1. Trigger drowsiness alert
2. Immediately trigger again (before cooldown expires)
3. Wait cooldown period
4. Trigger again

**Expected:**
- First alert triggers and sounds
- Second alert (within cooldown) doesn't sound
- After cooldown, alert sounds again

**Measurement:**
- [ ] First alert time: _____
- [ ] Second attempt time: _____
- [ ] Alert suppressed: Yes / No
- [ ] Cooldown duration: _____ seconds
- [ ] Third alert after cooldown: Yes / No

**Success Criteria:**
- ✅ Alert cooldown working (10s for drowsy, 15s for yawn)
- ✅ No repeated alerts within cooldown window
- ✅ Alert resumes after cooldown

---

## Phase 6: Dashboard Integration (20 minutes)

### Test 6.1: Backend Connection
**Command:**
```bash
python dashboard_backend/mqtt_listener.py
```

**Expected Output:**
```
[MQTT] Connected to 192.168.1.100:1883
[MQTT] Subscribed to topic: vehicle/driver/status
[MQTT] Received: {"status":"NORMAL",...}
```

**Measurement:**
- [ ] Backend starts: Yes / No
- [ ] MQTT connects: Yes / No
- [ ] Messages received: Yes / No

**Success Criteria:**
- ✅ Listener starts without errors
- ✅ MQTT connection confirmed
- ✅ Messages appearing every 2 seconds

---

### Test 6.2: Flask Dashboard
**Command:**
```bash
python dashboard/backend/app.py  # or app_with_mqtt.py
```

**Expected:**
```
Running on http://0.0.0.0:5000
```

**Steps:**
1. Open browser: http://localhost:5000
2. Check dashboard displays data
3. Trigger alert and verify dashboard updates

**Measurement:**
- [ ] Server starts: Yes / No
- [ ] Dashboard loads: Yes / No
- [ ] Real-time updates visible: Yes / No
- [ ] Updates lag time: _____ seconds

**Success Criteria:**
- ✅ Flask app runs without errors
- ✅ Dashboard page loads
- ✅ Data updates in real-time (<2s lag)

---

### Test 6.3: WebSocket Real-Time Updates
**Steps:**
1. Dashboard open in browser
2. Open browser DevTools → Network → WS
3. Trigger alert on ESP32
4. Watch WebSocket messages

**Expected:**
- WebSocket connection established
- Messages arrive every 2 seconds
- Alert broadcast when triggered

**Measurement:**
- [ ] WebSocket connected: Yes / No
- [ ] Message frequency: _____ seconds
- [ ] Alert message received: Yes / No

**Success Criteria:**
- ✅ WebSocket connects
- ✅ Real-time messages visible
- ✅ No disconnections during test
- ✅ Alerts broadcast immediately

---

## Phase 7: System Stability (60 minutes)

### Test 7.1: 30-Minute Stability Run
**Setup:**
1. All systems running (ESP32, MQTT, dashboard)
2. Monitor for crashes or disconnects
3. Check memory usage

**Monitoring Commands:**
```bash
# Terminal 1: MQTT monitor
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" | tee mqtt_log.txt

# Terminal 2: Dashboard
python dashboard/backend/app.py

# Terminal 3: Serial monitor
platformio device monitor -e esp32cam
```

**Record every 5 minutes:**
- [ ] Minute 0: System status: _____ (RUNNING/ERROR)
- [ ] Minute 5: MQTT messages: _____ (receiving/dropped)
- [ ] Minute 10: Memory usage: _____ KB
- [ ] Minute 15: Dashboard: _____ (updating/stale)
- [ ] Minute 20: Alerts test: Trigger one, verify: _____
- [ ] Minute 25: WiFi status: _____ (connected/reconnecting)
- [ ] Minute 30: Final check: Overall status: _____

**Success Criteria:**
- ✅ No crashes or hangs
- ✅ Consistent MQTT publishing (every 2s)
- ✅ No memory growth
- ✅ Dashboard stays responsive
- ✅ WiFi stable throughout

---

## Summary & Sign-Off

### Test Results
- **Total Tests:** 70+
- **Passed:** _____
- **Failed:** _____
- **Success Rate:** _____%

### Issues Found
```
Issue 1: _____
  Severity: Critical / High / Medium / Low
  Resolution: _____

Issue 2: _____
  Severity: Critical / High / Medium / Low
  Resolution: _____
```

### Overall Assessment
- [ ] System READY FOR PRODUCTION
- [ ] System READY WITH ADJUSTMENTS
- [ ] System NEEDS FIXES

### Sign-Off
**Tested by:** ________________  
**Date:** ________________  
**Time:** ________________  
**Notes:** ________________________________________

---

## Next Steps

If all tests passing:
1. Deploy to production vehicle
2. Start real-world driver testing
3. Collect accuracy metrics
4. Adjust EAR/MAR thresholds if needed

If issues found:
1. Document in detail
2. Create bug fixes
3. Re-test affected modules
4. Rerun full test suite

