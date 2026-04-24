#ifndef CONFIG_H
#define CONFIG_H

// ============================================
// Driver Drowsiness Detection - ESP32 Config
// ============================================
// This ESP32 handles actuators (buzzer/LED/vibration) and GPS only.
// Face detection runs on the host dashboard backend (MediaPipe).
// ============================================

// Include secrets if available (gitignored)
#ifdef __has_include
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#endif

// WiFi Configuration
#ifndef WIFI_SSID
#define WIFI_SSID            "YOUR_WIFI_SSID"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD        "YOUR_WIFI_PASSWORD"
#endif
#define WIFI_MAX_RETRIES     20
#define WIFI_TIMEOUT_MS      10000

// MQTT Broker
#ifndef MQTT_BROKER
#define MQTT_BROKER          "192.168.1.100"
#endif
#define MQTT_PORT            1883
#define MQTT_CLIENT_ID       "esp32_controller"

// Topics
#define MQTT_ALERT_TOPIC     "vehicle/alerts"          // subscribe (host → ESP32)
#define MQTT_GPS_TOPIC       "vehicle/gps"             // publish  (ESP32 → host)
#define MQTT_STATUS_TOPIC    "vehicle/driver/status"   // detector publishes here

// GPS publish interval
#define GPS_PUBLISH_INTERVAL_MS 2000

// Hardware GPIO Pins
#define BUZZER_PIN           12
#define LED_PIN              4
#define VIBRATION_PIN        2

// Hardware Alert Durations (ms)
#define BUZZER_DURATION_MS       500
#define VIBRATION_DURATION_MS    1000
#define LED_BLINK_DURATION_MS    150
#define LED_BLINK_COUNT          5

// Hardware Enabled Flags
#define BUZZER_ENABLED       true
#define LED_ENABLED          true
#define VIBRATION_ENABLED    true

// GPS (Neo-6M on UART1)
#define GPS_RX_PIN           16
#define GPS_TX_PIN           17
#define GPS_BAUD_RATE        9600
#define GPS_UPDATE_INTERVAL_MS 1000

// Fallback GPS Coordinates
#define FALLBACK_LATITUDE    18.5204f
#define FALLBACK_LONGITUDE   73.8567f

// Serial Debug
#define BAUD_RATE            115200

#endif // CONFIG_H
