# Dashboard Backend Integration with ESP32

This document explains how to integrate the MQTT listener with your Flask dashboard.

## Architecture

```
ESP32-CAM                 MQTT Broker              Flask Dashboard
   │                          │                          │
   ├─ Face Detection         │                          │
   ├─ EAR/MAR Calculation    │                          │
   ├─ GPIO Alerts            │                          │
   └─ JSON via MQTT ──────→ :1883 ────→ mqtt_listener.py
                              │         └─→ SocketIO ──→ WebSocket
                              │                           └─→ Browser UI
```

## Files

- **mqtt_listener.py**: Standalone MQTT client that can be imported
- **app_with_mqtt.py**: Example Flask app with MQTT integration
- **Original dashboard**: Located in `dashboard/backend/` and `dashboard/frontend/`

## Setup

### 1. Install Dependencies

```bash
# MQTT and networking
pip install paho-mqtt

# Flask with WebSocket support
pip install flask flask-cors flask-socketio python-socketio python-engineio

# Optional: For better async performance
pip install python-engineio[asyncio]
```

Or use existing requirements:

```bash
pip install -r dashboard/backend/requirements.txt
```

### 2. Configure MQTT Connection

Set environment variables before running:

```bash
# Bash
export MQTT_BROKER="192.168.1.100"
export MQTT_PORT="1883"
export MQTT_TOPIC="vehicle/driver/status"

# Or Windows
set MQTT_BROKER=192.168.1.100
set MQTT_PORT=1883
set MQTT_TOPIC=vehicle/driver/status
```

### 3. Run the MQTT Listener Bridge

**Standalone (testing):**

```bash
python dashboard_backend/mqtt_listener.py
```

This will connect to the MQTT broker and print received messages.

**With Flask Dashboard:**

Replace the original `dashboard/backend/app.py` with `app_with_mqtt.py` or integrate the MQTT listener into your existing app.

```bash
# Option 1: Replace and run
cp dashboard_backend/app_with_mqtt.py dashboard/backend/app.py
python -m flask run --host=0.0.0.0

# Option 2: Run as separate service
python dashboard_backend/mqtt_listener.py &
python dashboard/backend/app.py
```

## Integration with Existing Flask App

### Step 1: Add MQTT Listener Import

In your `dashboard/backend/app.py`:

```python
from mqtt_listener import create_mqtt_listener

# Create MQTT listener
mqtt_listener = create_mqtt_listener(
    broker="192.168.1.100",
    port=1883,
    topic="vehicle/driver/status"
)
```

### Step 2: Register Data Callback

```python
def on_detection_data(data):
    # data contains: status, ear, mar, latitude, longitude, timestamp, alert_triggered
    print(f"Detection update: {data['status']}")
    
    # Update your dashboard state
    update_dashboard_state(data)
    
    # Broadcast to WebSocket clients
    socketio.emit('status_update', data, broadcast=True)

mqtt_listener.register_callback(on_detection_data)
```

### Step 3: Verify Connection

```python
# Check if MQTT is connected
if mqtt_listener.is_connected():
    print("Connected to ESP32 via MQTT")
else:
    print("Failed to connect to MQTT broker")
```

## API Endpoints

The example `app_with_mqtt.py` provides these endpoints:

### Status Endpoints

```bash
# Get current detection status
curl http://localhost:5000/api/status

# Get alert history (last 100 alerts)
curl http://localhost:5000/api/alerts

# Get MQTT configuration
curl http://localhost:5000/api/config

# Health check
curl http://localhost:5000/health
```

### WebSocket Events

Connect to WebSocket at `ws://localhost:5000/socket.io/`:

**Client → Server:**
- `request_status`: Request current status
- `request_history`: Request alert history

**Server → Client:**
- `status_update`: New detection data arrives
- `connection_lost`: Lost connection to ESP32
- `connection_restored`: Reconnected to ESP32
- `alert_history`: Alert history response

### JavaScript Example

```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script>
const socket = io('http://localhost:5000');

// Listen for status updates
socket.on('status_update', (data) => {
    console.log('Detection:', data.status);
    console.log('EAR:', data.ear.toFixed(3));
    console.log('MAR:', data.mar.toFixed(3));
    updateDashboardUI(data);
});

// Listen for connection events
socket.on('connection_lost', () => {
    console.warn('Lost connection to ESP32');
    updateConnectionStatus('Disconnected');
});

socket.on('connection_restored', () => {
    console.log('Reconnected to ESP32');
    updateConnectionStatus('Connected');
});

// Request current status
socket.emit('request_status');

// Request alert history
socket.emit('request_history');
socket.on('alert_history', (history) => {
    console.log('Alert history:', history);
    updateAlertTable(history);
});
</script>
```

## Data Format

### Incoming MQTT Message

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

**Fields:**
- **status**: Current driver state
  - `NORMAL`: Eyes open, mouth closed
  - `DROWSY`: Eyes closed (EAR < threshold)
  - `YAWN`: Mouth open (MAR > threshold)
  - `NO_FACE`: No face detected
  - `ALERT`: Any alert active
  
- **ear**: Eye Aspect Ratio (0.0 - 1.0)
  - ~0.35 → Eyes open
  - ~0.15 → Eyes closed
  - Threshold (config.h): 0.22
  
- **mar**: Mouth Aspect Ratio (0.0 - 1.0)
  - ~0.40 → Mouth closed
  - ~0.75 → Yawning/wide open
  - Threshold (config.h): 0.65
  
- **latitude/longitude**: Current GPS location
  
- **timestamp**: Unix timestamp of detection
  
- **alert_triggered**: Whether alert was just activated

## Monitoring & Debugging

### Check MQTT Broker Connection

```bash
# Test MQTT connectivity
mosquitto_pub -h 192.168.1.100 -t "test/topic" -m "hello"
mosquitto_sub -h 192.168.1.100 -t "vehicle/driver/status"

# Or with paho-mqtt
python -c "
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    print(f'{msg.topic}: {msg.payload}')

client = mqtt.Client()
client.on_message = on_message
client.connect('192.168.1.100', 1883, 60)
client.subscribe('vehicle/driver/status')
client.loop_forever()
"
```

### View Flask Logs

```bash
# Run with debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
python dashboard/backend/app.py
```

### Test MQTT Listener Standalone

```bash
python dashboard_backend/mqtt_listener.py
```

Output:
```
[MQTT] Connecting to localhost:1883...
[MQTT] Connected to localhost:1883
[MQTT] Subscribed to topic: vehicle/driver/status
[Callback] New detection: NORMAL
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | MQTT broker not running or wrong IP | Check broker is running: `systemctl status mosquitto` or verify IP |
| "No message for 30 seconds" | ESP32 not publishing or network issue | Check ESP32 serial log for WiFi/MQTT status |
| "TypeError: object is not subscriptable" | MQTT message format wrong | ESP32 must publish valid JSON to `vehicle/driver/status` |
| WebSocket not updating | Browser not connected | Check browser console for socket.io errors |
| "Permission denied" on serial | User not in dialout group | Run `sudo usermod -aG dialout $USER` |

## Production Deployment

### MQTT Broker (Mosquitto)

```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# Start service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Check status
sudo systemctl status mosquitto
```

### Flask App with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run
gunicorn --workers 4 \
  --worker-class=eventlet \
  --bind=0.0.0.0:5000 \
  dashboard.backend.app:app
```

### Systemd Service

Create `/etc/systemd/system/drowsiness-dashboard.service`:

```ini
[Unit]
Description=Driver Drowsiness Dashboard
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/IOT_proj
Environment="MQTT_BROKER=localhost"
Environment="MQTT_PORT=1883"
ExecStart=/usr/bin/python3 /home/pi/IOT_proj/dashboard/backend/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable drowsiness-dashboard
sudo systemctl start drowsiness-dashboard
```

## References

- [Paho MQTT Python Client](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)
- [Flask SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [MQTT Protocol](https://mqtt.org/)
- [Mosquitto Broker](https://mosquitto.org/)
