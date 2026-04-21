#include "hardware.h"
#include "config.h"
#include <driver/ledc.h>

HardwareAlerts::HardwareAlerts() 
    : buzzer_enabled(BUZZER_ENABLED),
      led_enabled(LED_ENABLED),
      vibration_enabled(VIBRATION_ENABLED) {}

void HardwareAlerts::init() {
    if (buzzer_enabled) {
        pinMode(BUZZER_PIN, OUTPUT);
        digitalWrite(BUZZER_PIN, LOW);
    }
    
    if (led_enabled) {
        pinMode(LED_PIN, OUTPUT);
        digitalWrite(LED_PIN, LOW);
    }
    
    if (vibration_enabled) {
        pinMode(VIBRATION_PIN, OUTPUT);
        digitalWrite(VIBRATION_PIN, LOW);
    }
    
    Serial.println("[Hardware] Alerts initialized");
}

void HardwareAlerts::trigger_alert(const char* alert_type) {
    int buzzer_cycles = (strcmp(alert_type, "drowsy") == 0) ? 3 : 2;
    
    if (buzzer_enabled) {
        _buzzer_pulse(buzzer_cycles);
    }
    
    if (vibration_enabled) {
        _vibrate();
    }
    
    if (led_enabled) {
        _blink_led();
    }
}

void HardwareAlerts::_buzzer_pulse(int cycles) {
    for (int i = 0; i < cycles; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(BUZZER_DURATION_MS);
        digitalWrite(BUZZER_PIN, LOW);
        delay(BUZZER_DURATION_MS);
    }
}

void HardwareAlerts::_vibrate() {
    digitalWrite(VIBRATION_PIN, HIGH);
    delay(VIBRATION_DURATION_MS);
    digitalWrite(VIBRATION_PIN, LOW);
}

void HardwareAlerts::_blink_led() {
    for (int i = 0; i < LED_BLINK_COUNT; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(LED_BLINK_DURATION_MS);
        digitalWrite(LED_PIN, LOW);
        delay(LED_BLINK_DURATION_MS);
    }
}

void HardwareAlerts::cleanup() {
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
    digitalWrite(VIBRATION_PIN, LOW);
    Serial.println("[Hardware] Cleanup complete");
}
