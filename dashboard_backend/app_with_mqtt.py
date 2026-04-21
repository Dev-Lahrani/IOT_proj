#!/usr/bin/env python3
"""
Flask app with MQTT integration for ESP32 drowsiness detection
Place this in dashboard/backend/app.py to replace HTTP with MQTT listener
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import threading
import time
from datetime import datetime
from collections import deque
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'dashboard_backend'))

from mqtt_listener import create_mqtt_listener

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'vehicle/driver/status')

# Data storage
alert_history = deque(maxlen=100)  # Keep last 100 alerts
current_status = {
    'status': 'UNKNOWN',
    'ear': 0.0,
    'mar': 0.0,
    'latitude': 0.0,
    'longitude': 0.0,
    'timestamp': 0,
    'alert_triggered': False,
    'last_update': None,
    'connection_status': 'disconnected'
}

mqtt_listener = None
update_lock = threading.Lock()

def on_mqtt_data(data):
    """Callback when MQTT message received"""
    global current_status
    
    with update_lock:
        current_status.update(data)
        current_status['last_update'] = datetime.now().isoformat()
        current_status['connection_status'] = 'connected'
        
        # Log alerts
        if data.get('alert_triggered'):
            alert_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': data.get('status'),
                'ear': data.get('ear'),
                'mar': data.get('mar'),
                'location': {
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude')
                }
            }
            alert_history.append(alert_entry)
            print(f"[Alert] {alert_entry}")
    
    # Broadcast to all connected WebSocket clients
    socketio.emit('status_update', data, namespace='/', broadcast=True)

def mqtt_connection_monitor():
    """Monitor MQTT connection status"""
    global mqtt_listener, current_status
    
    while True:
        time.sleep(5)
        
        if mqtt_listener and not mqtt_listener.is_connected():
            with update_lock:
                current_status['connection_status'] = 'disconnected'
                current_status['status'] = 'DISCONNECTED'
            
            socketio.emit('connection_lost', 
                         {'message': 'Lost connection to ESP32'}, 
                         namespace='/', broadcast=True)
        elif mqtt_listener:
            with update_lock:
                current_status['connection_status'] = 'connected'
            
            socketio.emit('connection_restored',
                         {'message': 'Reconnected to ESP32'},
                         namespace='/', broadcast=True)

# ============= Routes =============

@app.route('/')
def index():
    """Serve main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current detection status"""
    with update_lock:
        return jsonify(current_status.copy())

@app.route('/api/alerts')
def get_alerts():
    """Get alert history"""
    with update_lock:
        return jsonify(list(alert_history))

@app.route('/api/config')
def get_config():
    """Get MQTT configuration"""
    return jsonify({
        'mqtt_broker': MQTT_BROKER,
        'mqtt_port': MQTT_PORT,
        'mqtt_topic': MQTT_TOPIC,
        'status': current_status['connection_status']
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'mqtt_connected': mqtt_listener.is_connected() if mqtt_listener else False,
        'timestamp': datetime.now().isoformat()
    })

# ============= WebSocket Events =============

@socketio.on('connect', namespace='/')
def handle_connect():
    """Client connected to WebSocket"""
    print("[WebSocket] Client connected")
    
    # Send current status immediately
    with update_lock:
        emit('status_update', current_status.copy())

@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    """Client disconnected from WebSocket"""
    print("[WebSocket] Client disconnected")

@socketio.on('request_status', namespace='/')
def handle_request_status():
    """Client requested current status"""
    with update_lock:
        emit('status_update', current_status.copy())

@socketio.on('request_history', namespace='/')
def handle_request_history():
    """Client requested alert history"""
    with update_lock:
        emit('alert_history', list(alert_history))

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# ============= Initialization =============

def init_mqtt():
    """Initialize MQTT listener"""
    global mqtt_listener
    
    print(f"[MQTT] Initializing connection to {MQTT_BROKER}:{MQTT_PORT}")
    mqtt_listener = create_mqtt_listener(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)
    
    if mqtt_listener.is_connected():
        print("[MQTT] Successfully connected")
        mqtt_listener.register_callback(on_mqtt_data)
        current_status['connection_status'] = 'connected'
    else:
        print("[MQTT] Failed to connect (will retry)")
        current_status['connection_status'] = 'disconnected'
    
    # Start connection monitor
    monitor_thread = threading.Thread(target=mqtt_connection_monitor, daemon=True)
    monitor_thread.start()

# ============= Main =============

if __name__ == '__main__':
    # Initialize MQTT
    init_mqtt()
    
    # Start Flask-SocketIO app
    print("[Server] Starting Flask application on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
