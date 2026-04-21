#ifndef HARDWARE_H
#define HARDWARE_H

#include <Arduino.h>
#include <driver/ledc.h>

class HardwareAlerts {
public:
    HardwareAlerts();
    void init();
    void trigger_alert(const char* alert_type = "drowsy");
    void cleanup();
    
private:
    bool buzzer_enabled;
    bool led_enabled;
    bool vibration_enabled;
    
    void _buzzer_pulse(int cycles);
    void _vibrate();
    void _blink_led();
};

#endif // HARDWARE_H
