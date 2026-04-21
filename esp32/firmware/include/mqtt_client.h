#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

typedef struct {
    const char* status;
    float ear;
    float mar;
    float latitude;
    float longitude;
    long timestamp;
    bool alert_triggered;
} DetectionData;

class MQTTPublisher {
public:
    MQTTPublisher();
    void init(const char* broker, int port);
    bool connect_wifi(const char* ssid, const char* password);
    bool connect_mqtt();
    void ensure_connected();
    void publish_detection(const DetectionData& data);
    void cleanup();
    
private:
    WiFiClient wifi_client;
    PubSubClient mqtt_client;
    const char* broker_address;
    int broker_port;
    bool wifi_connected;
    bool mqtt_connected;
    unsigned long last_connection_attempt;
};

#endif // MQTT_CLIENT_H
