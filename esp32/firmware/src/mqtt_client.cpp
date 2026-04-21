#include "mqtt_client.h"
#include "config.h"
#include <ArduinoJson.h>

MQTTPublisher::MQTTPublisher() 
    : mqtt_client(wifi_client),
      broker_address(MQTT_BROKER),
      broker_port(MQTT_PORT),
      wifi_connected(false),
      mqtt_connected(false),
      last_connection_attempt(0) {}

void MQTTPublisher::init(const char* broker, int port) {
    broker_address = broker;
    broker_port = port;
    mqtt_client.setServer(broker, port);
    Serial.printf("[MQTT] Client initialized for %s:%d\n", broker, port);
}

bool MQTTPublisher::connect_wifi(const char* ssid, const char* password) {
    Serial.printf("[WiFi] Connecting to %s...\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_MAX_RETRIES) {
        delay(1000);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        wifi_connected = true;
        Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    } else {
        wifi_connected = false;
        Serial.println("\n[WiFi] Failed to connect");
        return false;
    }
}

bool MQTTPublisher::connect_mqtt() {
    if (!wifi_connected) {
        return false;
    }
    
    if (mqtt_client.connected()) {
        mqtt_connected = true;
        return true;
    }
    
    if (millis() - last_connection_attempt < 5000) {
        return false;
    }
    
    last_connection_attempt = millis();
    Serial.printf("[MQTT] Connecting to %s:%d...\n", broker_address, broker_port);
    
    if (mqtt_client.connect(MQTT_CLIENT_ID)) {
        mqtt_connected = true;
        Serial.println("[MQTT] Connected!");
        return true;
    } else {
        mqtt_connected = false;
        Serial.printf("[MQTT] Failed, rc=%d\n", mqtt_client.state());
        return false;
    }
}

void MQTTPublisher::ensure_connected() {
    if (!wifi_connected) {
        Serial.println("[System] WiFi disconnected, attempting reconnect...");
        connect_wifi(WIFI_SSID, WIFI_PASSWORD);
    }
    
    if (wifi_connected && !mqtt_connected) {
        connect_mqtt();
    }
    
    if (mqtt_connected) {
        mqtt_client.loop();
    }
}

void MQTTPublisher::publish_detection(const DetectionData& data) {
    if (!mqtt_connected) {
        return;
    }
    
    StaticJsonDocument<256> doc;
    doc["status"] = data.status;
    doc["ear"] = serialized(String(data.ear, 3));
    doc["mar"] = serialized(String(data.mar, 3));
    doc["latitude"] = serialized(String(data.latitude, 6));
    doc["longitude"] = serialized(String(data.longitude, 6));
    doc["timestamp"] = data.timestamp;
    doc["alert_triggered"] = data.alert_triggered;
    
    String payload;
    serializeJson(doc, payload);
    
    if (mqtt_client.publish(MQTT_TOPIC, payload.c_str())) {
        Serial.printf("[MQTT] Published: %s\n", payload.c_str());
    } else {
        Serial.println("[MQTT] Publish failed");
        mqtt_connected = false;
    }
}

void MQTTPublisher::cleanup() {
    if (mqtt_connected) {
        mqtt_client.disconnect();
    }
    if (wifi_connected) {
        WiFi.disconnect();
    }
    Serial.println("[MQTT] Cleanup complete");
}
