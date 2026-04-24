#ifndef HARDWARE_H
#define HARDWARE_H

#include <Arduino.h>
#include <driver/ledc.h>

class HardwareAlerts {
public:
    HardwareAlerts();
    void init();
    void trigger_alert(const char* alert_type = "drowsy");
    void update();  // Call in loop() for non-blocking operation
    void cleanup();
    
private:
    bool buzzer_enabled;
    bool led_enabled;
    bool vibration_enabled;
    
    // Non-blocking alert state machine
    enum AlertPhase { IDLE, BUZZER_ON, BUZZER_OFF, VIBRATING, LED_ON, LED_OFF };
    AlertPhase current_phase;
    int buzzer_cycles_remaining;
    int led_blinks_remaining;
    unsigned long phase_start_time;
    const char* alert_type;
    
    void _start_buzzer_phase();
    void _start_vibration_phase();
    void _start_led_phase();
};

#endif // HARDWARE_H
