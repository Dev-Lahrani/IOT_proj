#ifndef CONFIG_H
#define CONFIG_H

// ============================================
// Driver Drowsiness Detection - ESP32 Config
// ============================================

// WiFi Configuration
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"
#define WIFI_MAX_RETRIES 5
#define WIFI_TIMEOUT_MS 10000

// MQTT Configuration
#define MQTT_BROKER "192.168.1.100"
#define MQTT_PORT 1883
#define MQTT_TOPIC "vehicle/driver/status"
#define MQTT_CLIENT_ID "esp32_drowsiness_detector"
#define MQTT_PUBLISH_INTERVAL_MS 2000

// Detection Thresholds
#define EAR_THRESHOLD 0.22f
#define MAR_THRESHOLD 0.65f
#define EAR_CONSECUTIVE_FRAMES 20
#define MAR_CONSECUTIVE_FRAMES 15
#define FRAME_SKIP 2
#define CLOSED_FRAMES_THRESHOLD 10

// Hardware GPIO Pins (ESP32-CAM)
#define BUZZER_PIN 12
#define LED_PIN 4
#define VIBRATION_PIN 2

// Hardware Alert Durations (ms)
#define BUZZER_DURATION_MS 500
#define VIBRATION_DURATION_MS 1000
#define LED_BLINK_DURATION_MS 150
#define LED_BLINK_COUNT 5

// Hardware Enabled Flags
#define BUZZER_ENABLED true
#define LED_ENABLED true
#define VIBRATION_ENABLED true

// GPS Configuration
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
#define GPS_BAUD_RATE 9600
#define GPS_UPDATE_INTERVAL_MS 1000

// Fallback GPS Coordinates (when GPS unavailable)
#define FALLBACK_LATITUDE 18.5204f
#define FALLBACK_LONGITUDE 73.8567f

// Camera Configuration
#define CAMERA_WIDTH 320
#define CAMERA_HEIGHT 240
#define CAMERA_JPEG_QUALITY 12

// Alert Cooldown (seconds)
#define DROWSY_ALERT_COOLDOWN 10
#define YAWN_ALERT_COOLDOWN 15

// Serial Debug
#define DEBUG_SERIAL true
#define BAUD_RATE 115200

// Face Detection Model
#define FACE_DETECTION_SCALE_FACTOR 1.1f
#define FACE_DETECTION_MIN_NEIGHBORS 5
#define FACE_DETECTION_MIN_SIZE 40

#endif // CONFIG_H
