# Testing & Validation Guide

This document covers all testing steps to validate the ESP32 Drowsiness Detection System before deployment.

## Pre-Testing Checklist

- [ ] ESP32-CAM firmware built successfully
- [ ] Hardware connected (GPIO pins, GPS, buzzer, LED, motor)
- [ ] MQTT broker running and accessible
- [ ] Dashboard backend code ready
- [ ] WiFi network available (2.4GHz)
- [ ] Serial console monitor ready
- [ ] Test scenario planned (video with driver)

## Phase 1: Firmware Upload & Connection

### Test 1.1: Successful Firmware Upload

**Steps:**
1. Connect ESP32-CAM to USB-to-Serial adapter
2. Put device in programming mode (GPIO0 to GND)
3. Run `platformio run -e esp32cam -t upload`
4. Verify output: `[✓] Firmware flashed successfully`

**Success Criteria:**
- ✅ No compilation errors
- ✅ Upload completes without timeout
- ✅ Hard reset message appears

**Debugging:**
- If failed: Check USB driver, serial port, power supply

### Test 1.2: Serial Monitor Connection

**Steps:**
1. Keep device in normal mode (GPIO0 NOT to GND)
2. Run `platformio device monitor -e esp32cam -b 115200`
3. Press Reset button
4. Watch for startup messages

**Success Criteria:**
- ✅ System startup message appears
- ✅ Hardware initialization messages visible
- ✅ No garbage data (correct baud rate)

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

## Phase 2: Hardware I/O Testing

### Test 2.1: GPIO Initialization

**Verify from Serial Monitor:**
```
[Hardware] Alerts initialized
[Hardware] GPIO setup complete
```

**Steps:**
1. Watch serial output for initialization
2. Check for any GPIO errors

**Success Criteria:**
- ✅ No GPIO initialization errors
- ✅ All three pins (buzzer, LED, vibration) initialized

### Test 2.2: Buzzer Alert

**Steps:**
1. Connect buzzer to GPIO 12 (and GND)
2. Modify config.h temporarily:
   ```cpp
   #define BUZZER_ENABLED true
   #define LED_ENABLED false
   #define VIBRATION_ENABLED false
   ```
3. Recompile and upload
4. Connect serial monitor
5. Look for alert trigger in logs (or force by manipulating data)

**Success Criteria:**
- ✅ Buzzer makes sound when alert triggered
- ✅ Correct number of pulses (3 for drowsy, 2 for yawn)
- ✅ Each pulse lasts ~500ms with gap between

**Measurement:**
- Drowsy alert: 3 beeps (500ms each)
- Yawn alert: 2 beeps (500ms each)

### Test 2.3: LED Alert

**Steps:**
1. Connect LED to GPIO 4 (and GND through current limiting resistor)
2. Trigger alert
3. Observe LED behavior

**Success Criteria:**
- ✅ LED blinks 5 times when alert triggered
- ✅ Each blink is ~150ms ON / 150ms OFF

### Test 2.4: Vibration Motor Alert

**Steps:**
1. Connect vibration motor to GPIO 2 (requires transistor/relay)
2. Trigger alert
3. Feel or observe motor vibration

**Success Criteria:**
- ✅ Motor vibrates when alert triggered
- ✅ Vibration duration is ~1 second
- ✅ No stuttering or incomplete cycles

## Phase 3: GPS Testing

### Test 3.1: GPS Serial Connection

**Steps:**
1. Connect GPS module (Neo-6M) on UART1:
   - RX (module) → GPIO 16
   - TX (module) → GPIO 17
   - GND/5V properly connected
2. Watch serial monitor for GPS initialization

**Success Criteria:**
- ✅ Serial output shows: `[GPS] Initialized on UART1`
- ✅ No UART errors

### Test 3.2: GPS Data Reading

**Outdoor Setup:**
1. Place ESP32 outdoors with GPS antenna exposed to sky
2. Wait 2-3 minutes for GPS lock
3. Watch serial monitor for coordinate updates

**Expected Behavior:**
```
[GPS] Updated: 18.5204, 73.8567
[GPS] Updated: 18.5205, 73.8568
```

**Success Criteria:**
- ✅ Coordinates appear after 2-3 minutes
- ✅ Coordinates are reasonable (not 0,0)
- ✅ Coordinates change slightly (showing real data)

**Debugging:**
- If no signal: Move antenna higher, ensure clear sky view
- If stuck coordinates: Check UART pins, GPS module connection
- If wrong values: Check NMEA parsing (verify RX/TX not swapped)

### Test 3.3: GPS Fallback

**Steps:**
1. Indoors where GPS has no signal
2. Watch logs - should see fallback coordinates from config.h

**Success Criteria:**
- ✅ System doesn't hang when GPS unavailable
- ✅ Fallback coordinates appear in MQTT messages
- ✅ Detection continues normally

**Expected Log:**
```
[GPS] Timeout, using fallback coordinates
[GPS] Updated: 18.5204, 73.8567 (fallback)
```

## Phase 4: WiFi & MQTT Testing

### Test 4.1: WiFi Connection

**Steps:**
1. Ensure config.h has correct SSID/password
2. Watch serial monitor
3. Should see connection attempt and IP address

**Expected Output:**
```
[WiFi] Connecting to MY_NETWORK...
[WiFi] Connected! IP: 192.168.1.123
```

**Success Criteria:**
- ✅ Connects within 10 seconds
- ✅ IP address assigned (not 0.0.0.0)
- ✅ SSID and IP are correct

**Debugging:**
- Wrong password: Check config.h and WiFi credentials
- No network found: Ensure 2.4GHz network (not 5GHz)
- Timeout: Check WiFi signal strength, router settings
- Multiple retries: Add delay between connection attempts

### Test 4.2: MQTT Broker Connection

**Prerequisite:** MQTT broker running on configured IP:port

```bash
# Verify broker is running
mosquitto_pub -h 192.168.1.100 -t test -m hello
```

**Steps:**
1. Verify WiFi connects first
2. Watch serial for MQTT connection

**Expected Output:**
```
[WiFi] Connected! IP: 192.168.1.123
[MQTT] Connecting to 192.168.1.100:1883...
[MQTT] Connected!
```

**Success Criteria:**
- ✅ MQTT connects within 30 seconds
- ✅ Broker IP and port match config.h
- ✅ No connection refused errors

### Test 4.3: MQTT Message Publishing

**Steps:**
1. ESP32 running and connected to MQTT
2. On another machine, subscribe to MQTT topic:
   ```bash
   mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" -v
   ```
3. Watch for incoming messages every 2 seconds

**Expected Output:**
```
vehicle/driver/status {"status":"NORMAL","ear":0.350,"mar":0.400,"latitude":18.5204,"longitude":73.8567,"timestamp":1234567890,"alert_triggered":false}
vehicle/driver/status {"status":"NORMAL","ear":0.340,"mar":0.405,"latitude":18.5204,"longitude":73.8567,"timestamp":1234567892,"alert_triggered":false}
```

**Success Criteria:**
- ✅ Messages arrive every ~2 seconds
- ✅ JSON format is valid
- ✅ All fields present (status, EAR, MAR, lat/lon, timestamp)
- ✅ No parsing errors

**Debugging:**
- No messages: Check MQTT connection, verify topic name
- Malformed JSON: Check ArduinoJson library, increase buffer size
- Wrong timestamps: Verify ESP32 system time (set via NTP if possible)

## Phase 5: Face Detection Testing

### Test 5.1: Face Detection Accuracy

**Setup:**
1. Position camera at typical driving position
2. Show driver's face clearly
3. Verify detection in serial output

**Expected Output:**
```
[Detection] Face detected!
[System] Monitoring driver...
```

**Success Criteria:**
- ✅ Face detected on first attempt
- ✅ No false positives (detecting non-faces)
- ✅ Detection works at different angles/lighting

### Test 5.2: EAR Calculation (Eyes Open/Closed)

**Test Sequence:**
1. **Eyes Open**: Normal position
   - Expected EAR: ~0.35-0.40
   - Log should show: `"ear":0.35`

2. **Eyes Closed**: Close both eyes
   - Expected EAR: ~0.10-0.20
   - Should trigger alert after 20 frames (~4 seconds at 5 FPS)
   - Log: `[Detection] Drowsiness detected! EAR=0.15`

3. **Yawning Suppression**: Blink normally
   - EAR drops, but not for 20 consecutive frames
   - Should NOT trigger alert
   - Alert cooldown prevents repeated alerts (10 second gap)

**Success Criteria:**
- ✅ EAR values reasonable (0.0-1.0 range)
- ✅ Eyes open: EAR ~0.35-0.40
- ✅ Eyes closed: EAR ~0.10-0.20
- ✅ Alert triggers after threshold
- ✅ Alert cooldown working (10s delay)

### Test 5.3: MAR Calculation (Yawning Detection)

**Test Sequence:**
1. **Mouth Closed**: Normal mouth position
   - Expected MAR: ~0.30-0.40
   - Log should show: `"mar":0.35`

2. **Mouth Open (Yawning)**: Open mouth wide
   - Expected MAR: ~0.65-0.80
   - Should trigger alert after 15 frames (~3 seconds)
   - Log: `[Detection] Yawning detected! MAR=0.70`

3. **Normal Talking**: Speak normally
   - MAR fluctuates but not sustained
   - Should NOT trigger yawn alert
   - Different from yawning pattern

**Success Criteria:**
- ✅ MAR values reasonable (0.0-1.0 range)
- ✅ Mouth closed: MAR ~0.30-0.40
- ✅ Mouth open: MAR ~0.65-0.80
- ✅ Yawn alert triggers after threshold
- ✅ Alert cooldown working (15s gap)

### Test 5.4: Edge Cases

**No Face:**
- Look away from camera
- Expected: `"status":"NO_FACE"`
- EAR/MAR: 0.0
- Alert: Not triggered

**Partial Face:**
- Cover half of face
- Expected: No face detected (or poor accuracy)
- Behavior: Graceful degradation

**Poor Lighting:**
- Dim lighting / backlit
- Expected: Detection still works or fails gracefully
- No crashes or hangs

**Multiple Faces:**
- Two people in frame
- Expected: Largest face detected
- Alert: Triggered for that person

## Phase 6: Dashboard Integration Testing

### Test 6.1: Backend Connection

**Steps:**
1. Start MQTT broker:
   ```bash
   mosquitto
   ```

2. Start dashboard backend with MQTT listener:
   ```bash
   python dashboard_backend/mqtt_listener.py
   ```

3. Verify connection message:
   ```
   [MQTT] Connected to 192.168.1.100:1883
   [MQTT] Subscribed to topic: vehicle/driver/status
   ```

**Success Criteria:**
- ✅ MQTT listener starts without errors
- ✅ Connection confirms
- ✅ Topic subscribed correctly

### Test 6.2: Data Flow (MQTT → Backend)

**Steps:**
1. MQTT listener running
2. ESP32 publishing messages
3. Watch listener output:
   ```
   [MQTT] Received: {"status":"NORMAL","ear":0.35,...}
   [MQTT] Received: {"status":"NORMAL","ear":0.34,...}
   ```

**Success Criteria:**
- ✅ Messages arrive every 2 seconds
- ✅ No parsing errors
- ✅ Callback triggered with data

### Test 6.3: WebSocket Broadcasting

**Steps:**
1. Backend + listener running
2. Connect browser to `http://localhost:5000`
3. Open browser DevTools → Network → WS
4. Trigger alert on ESP32
5. Watch WebSocket messages

**Expected:**
- Initial connection message
- Status updates every 2 seconds
- Alert broadcast when triggered

**Success Criteria:**
- ✅ WebSocket connects successfully
- ✅ Real-time messages appear
- ✅ No disconnections
- ✅ All fields displayed correctly

### Test 6.4: Alert History

**Steps:**
1. Dashboard open in browser
2. Trigger multiple alerts (close eyes, yawn)
3. Check `/api/alerts` endpoint

```bash
curl http://localhost:5000/api/alerts | jq
```

**Expected Output:**
```json
[
  {
    "timestamp": "2024-04-21T17:40:00",
    "status": "DROWSY",
    "ear": 0.15,
    "location": {"lat": 18.5204, "lon": 73.8567}
  },
  {
    "timestamp": "2024-04-21T17:41:00",
    "status": "YAWN",
    "mar": 0.70,
    "location": {"lat": 18.5204, "lon": 73.8567}
  }
]
```

**Success Criteria:**
- ✅ Alerts logged with timestamps
- ✅ Last 100 alerts retained
- ✅ Location data included

## Phase 7: Full System Integration Test

### Test 7.1: End-to-End Scenario

**Setup:**
1. ESP32-CAM firmware running
2. MQTT broker running
3. Dashboard backend running
4. Browser open to dashboard

**Test Sequence:**
1. Driver looks at camera (normal)
   - ✅ Dashboard shows: Status = NORMAL
   - ✅ EAR ~0.35, MAR ~0.35

2. Driver closes eyes for 5+ seconds
   - ✅ Buzzer sounds (3 pulses)
   - ✅ LED blinks 5 times
   - ✅ Motor vibrates
   - ✅ Dashboard shows: Status = DROWSY
   - ✅ Alert logged to history

3. Driver opens eyes
   - ✅ Alerts stop
   - ✅ Dashboard shows: Status = NORMAL

4. Driver yawns for 3+ seconds
   - ✅ Buzzer sounds (2 pulses)
   - ✅ LED blinks
   - ✅ Motor vibrates
   - ✅ Dashboard shows: Status = YAWN
   - ✅ Alert logged

5. Driver looks away
   - ✅ Dashboard shows: Status = NO_FACE
   - ✅ Alerts don't trigger

6. Driver returns to camera
   - ✅ Detection resumes normally

**Success Criteria:**
- ✅ All 6 sub-tests pass
- ✅ No crashes or hangs
- ✅ Real-time updates on dashboard
- ✅ Proper alert sequence and timing

### Test 7.2: Stress Test (30 minutes)

**Setup:** Same as end-to-end

**Test:**
1. Let system run continuously for 30 minutes
2. Monitor for:
   - Memory leaks (heap usage growing)
   - Dropped MQTT messages
   - WebSocket disconnections
   - Frozen interface

**Success Criteria:**
- ✅ No memory growth over 30 minutes
- ✅ MQTT message frequency stays constant
- ✅ No WebSocket reconnects
- ✅ Dashboard responsive

**Monitoring:**
```bash
# Check heap usage
curl http://localhost:5000/health | jq

# Monitor MQTT messages
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status" | wc -l
```

## Test Results Documentation

### Checklist

Use this to document all test results:

```
## Test Results - [Date]

### Phase 1: Firmware Upload
- [ ] Test 1.1 PASSED - Firmware uploads successfully
- [ ] Test 1.2 PASSED - Serial monitor receives startup messages

### Phase 2: Hardware I/O
- [ ] Test 2.1 PASSED - GPIO initialized
- [ ] Test 2.2 PASSED - Buzzer works (3 pulses drowsy, 2 pulses yawn)
- [ ] Test 2.3 PASSED - LED blinks 5 times
- [ ] Test 2.4 PASSED - Vibration motor activates 1 second

### Phase 3: GPS
- [ ] Test 3.1 PASSED - GPS serial initialized
- [ ] Test 3.2 PASSED - GPS coordinates received (outdoor)
- [ ] Test 3.3 PASSED - Fallback coordinates work (indoor)

### Phase 4: WiFi/MQTT
- [ ] Test 4.1 PASSED - WiFi connects
- [ ] Test 4.2 PASSED - MQTT connects
- [ ] Test 4.3 PASSED - Messages published every 2 seconds

### Phase 5: Face Detection
- [ ] Test 5.1 PASSED - Face detected correctly
- [ ] Test 5.2 PASSED - EAR calculation accurate, drowsiness alert works
- [ ] Test 5.3 PASSED - MAR calculation accurate, yawn alert works
- [ ] Test 5.4 PASSED - Edge cases handled gracefully

### Phase 6: Dashboard Integration
- [ ] Test 6.1 PASSED - Backend connects to MQTT
- [ ] Test 6.2 PASSED - Data flows ESP32 → Backend
- [ ] Test 6.3 PASSED - WebSocket broadcasts updates
- [ ] Test 6.4 PASSED - Alert history recorded

### Phase 7: Full Integration
- [ ] Test 7.1 PASSED - End-to-end scenario works perfectly
- [ ] Test 7.2 PASSED - Stable for 30 minutes (no crashes/leaks)

## Notes:
- Tested by: [Your Name]
- Device: [Device ID/Serial]
- Firmware Version: [Commit SHA]
- Issues Found: [None / List issues]
- Recommendations: [Any adjustments needed]
```

## Rollback Procedure

If critical issues found:

1. Keep the old Raspberry Pi code in `legacy_pi/`
2. To revert to Pi-based system:
   ```bash
   git checkout HEAD~1  # Go back one commit
   bash start.sh        # Run original system
   ```

3. Document issue in GitHub Issues
4. Create bug fix branch:
   ```bash
   git checkout -b fix/issue-name
   # ... fix code ...
   git push origin fix/issue-name
   ```

## Sign-Off

- [ ] All 7 phases tested and documented
- [ ] No critical issues remain
- [ ] Performance acceptable (no memory leaks)
- [ ] Ready for production deployment
- [ ] Instructions updated with any findings

**Tested by:** ________________  
**Date:** ________________  
**Approval:** ________________  

