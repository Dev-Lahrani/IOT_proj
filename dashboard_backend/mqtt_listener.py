#!/usr/bin/env python3
"""
MQTT Listener Bridge for ESP32 Drowsiness Detector
Receives MQTT messages from ESP32 and feeds data to Flask dashboard backend
"""

import json
import os
import threading
import time
import paho.mqtt.client as mqtt
import yaml
from datetime import datetime
from typing import Dict, Any, Callable

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "legacy_pi", "config.yaml",
)


def load_mqtt_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load MQTT settings from legacy_pi/config.yaml with safe defaults."""
    defaults = {
        "broker": "localhost",
        "port": 1883,
        "topic": "vehicle/driver/status",
    }
    try:
        with open(path, "r") as f:
            cfg = yaml.safe_load(f) or {}
        dash = cfg.get("dashboard", {}) or {}
        return {
            "broker": dash.get("mqtt_broker", defaults["broker"]),
            "port": int(dash.get("mqtt_port", defaults["port"])),
            "topic": dash.get("mqtt_topic", defaults["topic"]),
        }
    except FileNotFoundError:
        print(f"[MQTT] Config not found at {path}, using defaults")
        return defaults
    except Exception as e:
        print(f"[MQTT] Failed to read config ({e}), using defaults")
        return defaults

class MQTTListener:
    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.connected = False
        self.latest_data = {}
        self.data_lock = threading.Lock()
        self.data_callbacks = []
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected to {self.broker}:{self.port}")
            self.connected = True
            client.subscribe(self.topic)
            print(f"[MQTT] Subscribed to topic: {self.topic}")
        else:
            print(f"[MQTT] Connection failed with code {rc}")
            self.connected = False
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            
            # Add timestamp if not present
            if 'received_at' not in data:
                data['received_at'] = datetime.now().isoformat()
            
            with self.data_lock:
                self.latest_data = data
            
            # Trigger callbacks
            for callback in self.data_callbacks:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[Callback Error] {e}")
            
            print(f"[MQTT] Received: {json.dumps(data)}")
            
        except json.JSONDecodeError as e:
            print(f"[MQTT] Failed to parse JSON: {e}")
        except Exception as e:
            print(f"[MQTT] Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[MQTT] Disconnected with code {rc}")
        self.connected = False
    
    def connect(self):
        """Connect to MQTT broker"""
        print(f"[MQTT] Connecting to {self.broker}:{self.port}...")
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(30):
                if self.connected:
                    return True
                time.sleep(0.1)
            
            print("[MQTT] Connection timeout")
            return False
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            print("[MQTT] Disconnected")
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the latest received data"""
        with self.data_lock:
            return self.latest_data.copy()
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback function to be called on new data"""
        self.data_callbacks.append(callback)
    
    def is_connected(self) -> bool:
        """Check if MQTT is connected"""
        return self.connected


# Integration function for Flask app
def create_mqtt_listener(broker: str = "localhost", port: int = 1883, 
                        topic: str = "vehicle/driver/status") -> MQTTListener:
    """Factory function to create and connect MQTT listener"""
    listener = MQTTListener(broker, port, topic)
    listener.connect()
    return listener


if __name__ == "__main__":
    mqtt_cfg = load_mqtt_config()
    listener = create_mqtt_listener(
        broker=mqtt_cfg["broker"],
        port=mqtt_cfg["port"],
        topic=mqtt_cfg["topic"],
    )
    
    def on_data_received(data):
        print(f"[Callback] New detection: {data.get('status', 'UNKNOWN')}")
    
    listener.register_callback(on_data_received)
    
    # Keep running
    try:
        while listener.is_connected():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
        listener.disconnect()
