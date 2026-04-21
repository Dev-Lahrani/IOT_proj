#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include "gps.h"

typedef void (*AlertCallback)(const char* payload);

class MQTTPublisher {
public:
    MQTTPublisher();
    void init(const char* broker, int port, AlertCallback cb = nullptr);
    bool connect_wifi(const char* ssid, const char* password);
    bool connect_mqtt();
    void ensure_connected();
    void publish_gps(const GPSData& gps);
    void cleanup();

private:
    WiFiClient wifi_client;
    PubSubClient mqtt_client;
    const char* broker_address;
    int broker_port;
    bool wifi_connected;
    bool mqtt_connected;
    unsigned long last_connection_attempt;
    AlertCallback alert_callback;

    static MQTTPublisher* _instance;
    static void _static_callback(char* topic, byte* payload, unsigned int length);
};

#endif // MQTT_CLIENT_H
