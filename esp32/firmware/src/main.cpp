#include <Arduino.h>
#include "config.h"
#include "hardware.h"
#include "gps.h"
#include "mqtt_client.h"

HardwareAlerts hardware;
GPSReader gps_reader;
MQTTPublisher mqtt;

// Called by MQTT client when a message arrives on vehicle/alerts
void on_alert(const char* payload) {
    Serial.printf("[Alert] Received command: %s\n", payload);
    if (strstr(payload, "drowsy")) {
        hardware.trigger_alert("drowsy");
    } else if (strstr(payload, "yawn")) {
        hardware.trigger_alert("yawn");
    }
}

void setup() {
    Serial.begin(BAUD_RATE);
    delay(500);

    Serial.println("\n=====================================");
    Serial.println(" ESP32 Controller (actuators + GPS)");
    Serial.println("=====================================\n");

    hardware.init();
    gps_reader.init();
    mqtt.init(MQTT_BROKER, MQTT_PORT, on_alert);
    mqtt.connect_wifi(WIFI_SSID, WIFI_PASSWORD);
    mqtt.connect_mqtt();

    Serial.println("[System] Ready\n");
}

void loop() {
    mqtt.ensure_connected();
    hardware.update();  // Non-blocking alert updates

    static unsigned long last_gps_pub = 0;
    if (millis() - last_gps_pub >= GPS_PUBLISH_INTERVAL_MS) {
        GPSData gps = gps_reader.get_data();
        mqtt.publish_gps(gps);
        last_gps_pub = millis();
    }
}
