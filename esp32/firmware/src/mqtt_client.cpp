#include "mqtt_client.h"
#include "config.h"
#include <ArduinoJson.h>

MQTTPublisher* MQTTPublisher::_instance = nullptr;

MQTTPublisher::MQTTPublisher()
    : mqtt_client(wifi_client),
      broker_address(MQTT_BROKER),
      broker_port(MQTT_PORT),
      wifi_connected(false),
      mqtt_connected(false),
      last_connection_attempt(0),
      alert_callback(nullptr) {
    _instance = this;
}

void MQTTPublisher::_static_callback(char* topic, byte* payload, unsigned int length) {
    if (!_instance || !_instance->alert_callback) return;
    char buf[256];
    size_t len = min((size_t)length, sizeof(buf) - 1);
    memcpy(buf, payload, len);
    buf[len] = '\0';
    _instance->alert_callback(buf);
}

void MQTTPublisher::init(const char* broker, int port, AlertCallback cb) {
    broker_address = broker;
    broker_port = port;
    alert_callback = cb;
    mqtt_client.setServer(broker, port);
    mqtt_client.setCallback(_static_callback);
    Serial.printf("[MQTT] Client configured for %s:%d\n", broker, port);
}

bool MQTTPublisher::connect_wifi(const char* ssid, const char* password) {
    Serial.printf("[WiFi] Connecting to %s", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_MAX_RETRIES) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifi_connected = true;
        Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    }
    wifi_connected = false;
    Serial.println("\n[WiFi] Failed to connect");
    return false;
}

bool MQTTPublisher::connect_mqtt() {
    if (!wifi_connected) return false;
    if (mqtt_client.connected()) { mqtt_connected = true; return true; }
    if (millis() - last_connection_attempt < 5000) return false;

    last_connection_attempt = millis();
    Serial.printf("[MQTT] Connecting to %s:%d...\n", broker_address, broker_port);

    if (mqtt_client.connect(MQTT_CLIENT_ID)) {
        mqtt_connected = true;
        mqtt_client.subscribe(MQTT_ALERT_TOPIC);
        Serial.printf("[MQTT] Connected, subscribed to %s\n", MQTT_ALERT_TOPIC);
        return true;
    }
    mqtt_connected = false;
    Serial.printf("[MQTT] Failed rc=%d\n", mqtt_client.state());
    return false;
}

void MQTTPublisher::ensure_connected() {
    if (WiFi.status() != WL_CONNECTED) {
        wifi_connected = false;
        connect_wifi(WIFI_SSID, WIFI_PASSWORD);
    }
    if (wifi_connected && !mqtt_client.connected()) {
        mqtt_connected = false;
        connect_mqtt();
    }
    if (mqtt_connected) {
        mqtt_client.loop();
    }
}

void MQTTPublisher::publish_gps(const GPSData& gps) {
    if (!mqtt_connected) return;

    StaticJsonDocument<128> doc;
    doc["latitude"]  = gps.latitude;
    doc["longitude"] = gps.longitude;
    doc["valid"]     = gps.valid;
    doc["timestamp"] = (long)millis() / 1000;

    String payload;
    serializeJson(doc, payload);

    if (!mqtt_client.publish(MQTT_GPS_TOPIC, payload.c_str())) {
        mqtt_connected = false;
    }
    Serial.printf("[GPS] Published: %.4f, %.4f\n", gps.latitude, gps.longitude);
}

void MQTTPublisher::cleanup() {
    if (mqtt_connected) mqtt_client.disconnect();
    if (wifi_connected) WiFi.disconnect();
    Serial.println("[MQTT] Cleanup complete");
}
