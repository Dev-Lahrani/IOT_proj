import requests
import paho.mqtt.client as mqtt
import json
import time
import threading


class DataPublisher:
    """Publishes detection data to the dashboard backend."""

    def __init__(self, config):
        host = config.get("host", "127.0.0.1")
        if host in {"0.0.0.0", "::"}:
            host = "127.0.0.1"
        self.dashboard_url = f"http://{host}:{config['port']}/update"
        self.use_mqtt = config["use_mqtt"]
        self.push_interval = config["push_interval"]

        self._latest_data = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        if self.use_mqtt:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.connect(
                config["mqtt_broker"],
                config["mqtt_port"],
                60,
            )
            self.mqtt_topic = config["mqtt_topic"]
        else:
            self.mqtt_client = None

    def push(self, data):
        """Store latest data for periodic publishing."""
        with self._lock:
            self._latest_data = data

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def _publish_loop(self):
        while self._running:
            with self._lock:
                data = self._latest_data

            if data:
                try:
                    if self.use_mqtt and self.mqtt_client:
                        self.mqtt_client.publish(
                            self.mqtt_topic,
                            json.dumps(data),
                        )
                    else:
                        requests.post(
                            self.dashboard_url,
                            json=data,
                            timeout=3,
                        )
                except (requests.RequestException, ConnectionError):
                    pass

            time.sleep(self.push_interval)

    def stop(self):
        self._running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
