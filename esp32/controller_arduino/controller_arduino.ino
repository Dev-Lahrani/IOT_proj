/*
 * ESP32 Controller — single-file Arduino sketch
 *
 * Role: actuators (buzzer / LED / vibration) + Neo-6M GPS.
 * Network: WiFi "motorola", MQTT broker on laptop at 10.120.132.175:1883.
 *
 * MQTT topics:
 *   vehicle/alerts         (subscribe)  — "drowsy" or "yawn" commands from laptop
 *   vehicle/gps            (publish)    — GPS JSON every 2 s
 *
 * Upload (Arduino IDE):
 *   Board:          "ESP32 Dev Module"
 *   Upload speed:   921600
 *   Libraries:      PubSubClient (knolleary), ArduinoJson (bblanchon, v6.x)
 *
 * Wiring:
 *   Buzzer         GPIO 12
 *   LED            GPIO 4
 *   Vibration      GPIO 2
 *   Neo-6M TX  ->  GPIO 16 (ESP32 RX1)
 *   Neo-6M RX  <-  GPIO 17 (ESP32 TX1)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ============================================================
// Configuration
// ============================================================
#define WIFI_SSID            "motorola"
#define WIFI_PASSWORD        "edge50pro"
#define WIFI_MAX_RETRIES     20

#define MQTT_BROKER          "10.120.132.175"
#define MQTT_PORT            1883
#define MQTT_CLIENT_ID       "esp32_controller"

#define MQTT_ALERT_TOPIC     "vehicle/alerts"
#define MQTT_GPS_TOPIC       "vehicle/gps"

#define GPS_PUBLISH_INTERVAL_MS 2000

// Actuator pins
#define BUZZER_PIN           12
#define LED_PIN              4
#define VIBRATION_PIN        2

// Alert durations (ms)
#define BUZZER_DURATION_MS       500
#define VIBRATION_DURATION_MS    1000
#define LED_BLINK_DURATION_MS    150
#define LED_BLINK_COUNT          5

#define BUZZER_ENABLED       true
#define LED_ENABLED          true
#define VIBRATION_ENABLED    true

// GPS
#define GPS_RX_PIN           16
#define GPS_TX_PIN           17
#define GPS_BAUD_RATE        9600
#define GPS_UPDATE_INTERVAL_MS 1000

// Fallback coords (used until first valid GPS fix)
#define FALLBACK_LATITUDE    18.5204f
#define FALLBACK_LONGITUDE   73.8567f

#define BAUD_RATE            115200

// ============================================================
// GPS (Neo-6M on UART1, NMEA GPRMC parser)
// ============================================================
struct GPSData {
    float latitude;
    float longitude;
    bool  valid;
    unsigned long last_update;
};

HardwareSerial GPSSerial(1);
GPSData gps_data = { FALLBACK_LATITUDE, FALLBACK_LONGITUDE, false, 0 };
unsigned long gps_last_read = 0;

void gps_init() {
    GPSSerial.begin(GPS_BAUD_RATE, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
    Serial.println("[GPS] Initialized on UART1");
}

static String gps_read_line() {
    String line = "";
    while (GPSSerial.available()) {
        char c = GPSSerial.read();
        if (c == '\n') return line;
        if (c != '\r') line += c;
    }
    return "";
}

static bool gps_parse_gprmc(const String& sentence) {
    if (!sentence.startsWith("$GPRMC")) return false;

    int commas[12];
    int idx = 0;
    for (unsigned int i = 0; i < sentence.length() && idx < 12; i++) {
        if (sentence[i] == ',') commas[idx++] = i;
    }
    if (idx < 9) return false;

    String status = sentence.substring(commas[1] + 1, commas[2]);
    if (status != "A") return false;  // A=active, V=void

    String lat_str = sentence.substring(commas[2] + 1, commas[3]);
    String lat_dir = sentence.substring(commas[3] + 1, commas[4]);
    if (lat_str.length() < 4) return false;
    float lat_deg = lat_str.substring(0, 2).toFloat();
    float lat_min = lat_str.substring(2).toFloat();
    gps_data.latitude = lat_deg + (lat_min / 60.0f);
    if (lat_dir == "S") gps_data.latitude *= -1;

    String lon_str = sentence.substring(commas[4] + 1, commas[5]);
    String lon_dir = sentence.substring(commas[5] + 1, commas[6]);
    if (lon_str.length() < 5) return false;
    float lon_deg = lon_str.substring(0, 3).toFloat();
    float lon_min = lon_str.substring(3).toFloat();
    gps_data.longitude = lon_deg + (lon_min / 60.0f);
    if (lon_dir == "W") gps_data.longitude *= -1;

    gps_data.valid = true;
    gps_data.last_update = millis();
    return true;
}

void gps_update() {
    if (millis() - gps_last_read < GPS_UPDATE_INTERVAL_MS) return;
    String line = gps_read_line();
    if (line.length() > 0 && gps_parse_gprmc(line)) {
        Serial.printf("[GPS] Updated: %.4f, %.4f\n", gps_data.latitude, gps_data.longitude);
    }
    gps_last_read = millis();
}

// ============================================================
// Hardware alerts (non-blocking state machine)
// ============================================================
enum AlertPhase { IDLE, BUZZER_ON, BUZZER_OFF, VIBRATING, LED_ON, LED_OFF };
AlertPhase alert_phase = IDLE;
int buzzer_cycles_remaining = 0;
int led_blinks_remaining = 0;
unsigned long phase_start = 0;
const char* current_alert = nullptr;

void hw_init() {
    if (BUZZER_ENABLED)    { pinMode(BUZZER_PIN, OUTPUT);    digitalWrite(BUZZER_PIN, LOW); }
    if (LED_ENABLED)       { pinMode(LED_PIN, OUTPUT);       digitalWrite(LED_PIN, LOW); }
    if (VIBRATION_ENABLED) { pinMode(VIBRATION_PIN, OUTPUT); digitalWrite(VIBRATION_PIN, LOW); }
    Serial.println("[Hardware] Alerts initialized");
}

static void hw_start_led();
static void hw_start_vibration();

static void hw_start_buzzer() {
    if (!BUZZER_ENABLED) { hw_start_vibration(); return; }
    alert_phase = BUZZER_ON;
    phase_start = millis();
    digitalWrite(BUZZER_PIN, HIGH);
}

static void hw_start_vibration() {
    if (!VIBRATION_ENABLED) { hw_start_led(); return; }
    alert_phase = VIBRATING;
    phase_start = millis();
    digitalWrite(VIBRATION_PIN, HIGH);
}

static void hw_start_led() {
    if (!LED_ENABLED) {
        alert_phase = IDLE;
        Serial.printf("[Hardware] Alert '%s' complete\n", current_alert);
        return;
    }
    alert_phase = LED_ON;
    phase_start = millis();
    digitalWrite(LED_PIN, HIGH);
}

void hw_trigger(const char* alert_type) {
    if (alert_phase != IDLE) return;  // alert already running
    current_alert = alert_type;
    buzzer_cycles_remaining = (strcmp(alert_type, "drowsy") == 0) ? 3 : 2;
    led_blinks_remaining = LED_BLINK_COUNT;
    hw_start_buzzer();
}

void hw_update() {
    if (alert_phase == IDLE) return;
    unsigned long elapsed = millis() - phase_start;

    switch (alert_phase) {
        case BUZZER_ON:
            if (elapsed >= BUZZER_DURATION_MS) {
                digitalWrite(BUZZER_PIN, LOW);
                buzzer_cycles_remaining--;
                if (buzzer_cycles_remaining > 0) {
                    alert_phase = BUZZER_OFF;
                    phase_start = millis();
                } else {
                    hw_start_vibration();
                }
            }
            break;
        case BUZZER_OFF:
            if (elapsed >= BUZZER_DURATION_MS) hw_start_buzzer();
            break;
        case VIBRATING:
            if (elapsed >= VIBRATION_DURATION_MS) {
                digitalWrite(VIBRATION_PIN, LOW);
                hw_start_led();
            }
            break;
        case LED_ON:
            if (elapsed >= LED_BLINK_DURATION_MS) {
                digitalWrite(LED_PIN, LOW);
                led_blinks_remaining--;
                if (led_blinks_remaining > 0) {
                    alert_phase = LED_OFF;
                    phase_start = millis();
                } else {
                    alert_phase = IDLE;
                    Serial.printf("[Hardware] Alert '%s' complete\n", current_alert);
                }
            }
            break;
        case LED_OFF:
            if (elapsed >= LED_BLINK_DURATION_MS) hw_start_led();
            break;
        default: break;
    }
}

// ============================================================
// WiFi + MQTT
// ============================================================
WiFiClient wifi_client;
PubSubClient mqtt(wifi_client);
bool wifi_up = false;
bool mqtt_up = false;
unsigned long last_mqtt_attempt = 0;

void on_mqtt_message(char* topic, byte* payload, unsigned int length) {
    char buf[128];
    size_t len = min((size_t)length, sizeof(buf) - 1);
    memcpy(buf, payload, len);
    buf[len] = '\0';
    Serial.printf("[Alert] Received on %s: %s\n", topic, buf);
    if (strstr(buf, "drowsy"))      hw_trigger("drowsy");
    else if (strstr(buf, "yawn"))   hw_trigger("yawn");
}

bool wifi_connect() {
    Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int tries = 0;
    while (WiFi.status() != WL_CONNECTED && tries < WIFI_MAX_RETRIES) {
        delay(500);
        Serial.print(".");
        tries++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        wifi_up = true;
        Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    }
    wifi_up = false;
    Serial.println("\n[WiFi] Failed to connect");
    return false;
}

bool mqtt_connect() {
    if (!wifi_up) return false;
    if (mqtt.connected()) { mqtt_up = true; return true; }
    if (millis() - last_mqtt_attempt < 5000) return false;
    last_mqtt_attempt = millis();
    Serial.printf("[MQTT] Connecting to %s:%d...\n", MQTT_BROKER, MQTT_PORT);
    if (mqtt.connect(MQTT_CLIENT_ID)) {
        mqtt_up = true;
        mqtt.subscribe(MQTT_ALERT_TOPIC);
        Serial.printf("[MQTT] Connected, subscribed to %s\n", MQTT_ALERT_TOPIC);
        return true;
    }
    mqtt_up = false;
    Serial.printf("[MQTT] Failed rc=%d\n", mqtt.state());
    return false;
}

void mqtt_ensure_connected() {
    if (WiFi.status() != WL_CONNECTED) {
        if (wifi_up) Serial.println("[WiFi] Disconnected");
        wifi_up = false;
        wifi_connect();
    }
    if (wifi_up && !mqtt.connected()) {
        if (mqtt_up) Serial.println("[MQTT] Disconnected");
        mqtt_up = false;
        last_mqtt_attempt = 0;  // allow immediate reconnect
        mqtt_connect();
    }
    if (mqtt_up) mqtt.loop();
}

void mqtt_publish_gps() {
    if (!mqtt_up) return;
    JsonDocument doc;
    doc["latitude"]  = gps_data.latitude;
    doc["longitude"] = gps_data.longitude;
    doc["valid"]     = gps_data.valid;
    doc["timestamp"] = (long)millis() / 1000;
    String payload;
    serializeJson(doc, payload);
    if (!mqtt.publish(MQTT_GPS_TOPIC, payload.c_str())) {
        Serial.println("[MQTT] Publish failed, disconnecting");
        mqtt_up = false;
        last_mqtt_attempt = 0;
    } else {
        Serial.printf("[GPS] Published: %.4f, %.4f\n", gps_data.latitude, gps_data.longitude);
    }
}

// ============================================================
// setup() / loop()
// ============================================================
void setup() {
    Serial.begin(BAUD_RATE);
    delay(500);
    Serial.println("\n=====================================");
    Serial.println(" ESP32 Controller (actuators + GPS)");
    Serial.println("=====================================\n");

    hw_init();
    gps_init();
    mqtt.setServer(MQTT_BROKER, MQTT_PORT);
    mqtt.setCallback(on_mqtt_message);
    wifi_connect();
    mqtt_connect();

    Serial.println("[System] Ready\n");
}

void loop() {
    mqtt_ensure_connected();
    hw_update();
    gps_update();

    static unsigned long last_gps_pub = 0;
    if (millis() - last_gps_pub >= GPS_PUBLISH_INTERVAL_MS) {
        mqtt_publish_gps();
        last_gps_pub = millis();
    }
}
