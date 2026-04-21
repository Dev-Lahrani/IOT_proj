#include <Arduino.h>
#include "config.h"
#include "hardware.h"
#include "gps.h"
#include "mqtt_client.h"
#include "face_detector.h"

// Global objects
HardwareAlerts hardware;
GPSReader gps_reader;
MQTTPublisher mqtt_publisher;
FaceDetector face_detector;

// State tracking
int eye_closed_counter = 0;
int mouth_open_counter = 0;
const char* current_status = "NORMAL";
unsigned long last_alert_time_drowsy = 0;
unsigned long last_alert_time_yawn = 0;
int frame_count = 0;

void setup() {
    Serial.begin(BAUD_RATE);
    delay(1000);
    
    Serial.println("\n\n=====================================");
    Serial.println("ESP32 Drowsiness Detection System");
    Serial.println("=====================================\n");
    
    // Initialize hardware
    hardware.init();
    
    // Initialize GPS
    gps_reader.init();
    
    // Initialize camera
    face_detector.init_camera();
    
    // Initialize MQTT
    mqtt_publisher.init(MQTT_BROKER, MQTT_PORT);
    
    // Connect to WiFi
    if (!mqtt_publisher.connect_wifi(WIFI_SSID, WIFI_PASSWORD)) {
        Serial.println("[System] WiFi connection failed, will retry in loop");
    }
    
    // Connect to MQTT
    mqtt_publisher.connect_mqtt();
    
    Serial.println("[System] Setup complete, starting main loop\n");
}

void loop() {
    // Ensure WiFi and MQTT connections
    mqtt_publisher.ensure_connected();
    
    // Get camera frame
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        delay(100);
        return;
    }
    
    frame_count++;
    
    // Process every Nth frame (frame skip optimization)
    if (frame_count % FRAME_SKIP != 0) {
        esp_camera_fb_return(fb);
        return;
    }
    
    // Detect faces and calculate EAR/MAR
    DetectionResult detection = face_detector.process_frame(fb);
    esp_camera_fb_return(fb);
    
    if (!detection.face_detected) {
        current_status = "NO_FACE";
        eye_closed_counter = 0;
        mouth_open_counter = 0;
    } else {
        // Check for closed eyes (drowsiness)
        if (detection.ear < EAR_THRESHOLD) {
            eye_closed_counter++;
            if (eye_closed_counter >= EAR_CONSECUTIVE_FRAMES) {
                unsigned long now = millis() / 1000;
                if (now - last_alert_time_drowsy >= DROWSY_ALERT_COOLDOWN) {
                    current_status = "DROWSY";
                    hardware.trigger_alert("drowsy");
                    last_alert_time_drowsy = now;
                    Serial.printf("[Detection] Drowsiness detected! EAR=%.3f\n", detection.ear);
                }
                eye_closed_counter = CLOSED_FRAMES_THRESHOLD;
            }
        } else {
            if (eye_closed_counter > 0) {
                eye_closed_counter--;
            }
        }
        
        // Check for yawning (open mouth)
        if (detection.mar > MAR_THRESHOLD) {
            mouth_open_counter++;
            if (mouth_open_counter >= MAR_CONSECUTIVE_FRAMES) {
                unsigned long now = millis() / 1000;
                if (now - last_alert_time_yawn >= YAWN_ALERT_COOLDOWN) {
                    current_status = "YAWN";
                    hardware.trigger_alert("yawn");
                    last_alert_time_yawn = now;
                    Serial.printf("[Detection] Yawning detected! MAR=%.3f\n", detection.mar);
                }
                mouth_open_counter = CLOSED_FRAMES_THRESHOLD;
            }
        } else {
            if (mouth_open_counter > 0) {
                mouth_open_counter--;
            }
        }
        
        // Default status if no alerts
        if (current_status[0] == 'D' || current_status[0] == 'Y') {
            // Keep status until reset
        } else {
            current_status = "NORMAL";
        }
    }
    
    // Get GPS data
    GPSData gps_data = gps_reader.get_data();
    
    // Prepare and publish detection data
    static unsigned long last_publish = 0;
    if (millis() - last_publish >= MQTT_PUBLISH_INTERVAL_MS) {
        DetectionData data;
        data.status = current_status;
        data.ear = detection.ear;
        data.mar = detection.mar;
        data.latitude = gps_data.latitude;
        data.longitude = gps_data.longitude;
        data.timestamp = time(nullptr);
        data.alert_triggered = (current_status[0] == 'D' || current_status[0] == 'Y');
        
        mqtt_publisher.publish_detection(data);
        last_publish = millis();
    }
    
    delay(10);
}

void shutdown_handler() {
    Serial.println("\n[System] Shutting down...");
    hardware.cleanup();
    gps_reader.cleanup();
    face_detector.cleanup_camera();
    mqtt_publisher.cleanup();
    Serial.println("[System] Goodbye!");
}
