#include "hardware.h"
#include "config.h"
#include <Arduino.h>

HardwareAlerts::HardwareAlerts() 
    : buzzer_enabled(BUZZER_ENABLED),
      led_enabled(LED_ENABLED),
      vibration_enabled(VIBRATION_ENABLED),
      current_phase(IDLE),
      buzzer_cycles_remaining(0),
      led_blinks_remaining(0),
      phase_start_time(0),
      alert_type(nullptr) {}

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
    if (current_phase != IDLE) {
        return;  // Alert already in progress
    }
    
    this->alert_type = alert_type;
    buzzer_cycles_remaining = (strcmp(alert_type, "drowsy") == 0) ? 3 : 2;
    led_blinks_remaining = LED_BLINK_COUNT;
    
    _start_buzzer_phase();
}

void HardwareAlerts::update() {
    if (current_phase == IDLE) {
        return;
    }
    
    unsigned long elapsed = millis() - phase_start_time;
    
    switch (current_phase) {
        case BUZZER_ON:
            if (elapsed >= BUZZER_DURATION_MS) {
                digitalWrite(BUZZER_PIN, LOW);
                buzzer_cycles_remaining--;
                if (buzzer_cycles_remaining > 0) {
                    current_phase = BUZZER_OFF;
                    phase_start_time = millis();
                } else {
                    _start_vibration_phase();
                }
            }
            break;
            
        case BUZZER_OFF:
            if (elapsed >= BUZZER_DURATION_MS) {
                _start_buzzer_phase();
            }
            break;
            
        case VIBRATING:
            if (elapsed >= VIBRATION_DURATION_MS) {
                digitalWrite(VIBRATION_PIN, LOW);
                _start_led_phase();
            }
            break;
            
        case LED_ON:
            if (elapsed >= LED_BLINK_DURATION_MS) {
                digitalWrite(LED_PIN, LOW);
                led_blinks_remaining--;
                if (led_blinks_remaining > 0) {
                    current_phase = LED_OFF;
                    phase_start_time = millis();
                } else {
                    current_phase = IDLE;
                    Serial.printf("[Hardware] Alert '%s' complete\n", alert_type);
                }
            }
            break;
            
        case LED_OFF:
            if (elapsed >= LED_BLINK_DURATION_MS) {
                _start_led_phase();
            }
            break;
            
        default:
            break;
    }
}

void HardwareAlerts::_start_buzzer_phase() {
    if (!buzzer_enabled) {
        _start_vibration_phase();
        return;
    }
    current_phase = BUZZER_ON;
    phase_start_time = millis();
    digitalWrite(BUZZER_PIN, HIGH);
}

void HardwareAlerts::_start_vibration_phase() {
    if (!vibration_enabled) {
        _start_led_phase();
        return;
    }
    current_phase = VIBRATING;
    phase_start_time = millis();
    digitalWrite(VIBRATION_PIN, HIGH);
}

void HardwareAlerts::_start_led_phase() {
    if (!led_enabled) {
        current_phase = IDLE;
        Serial.printf("[Hardware] Alert '%s' complete\n", alert_type);
        return;
    }
    current_phase = LED_ON;
    phase_start_time = millis();
    digitalWrite(LED_PIN, HIGH);
}

void HardwareAlerts::cleanup() {
    if (buzzer_enabled)    digitalWrite(BUZZER_PIN, LOW);
    if (led_enabled)       digitalWrite(LED_PIN, LOW);
    if (vibration_enabled) digitalWrite(VIBRATION_PIN, LOW);
    current_phase = IDLE;
    Serial.println("[Hardware] Cleanup complete");
}
