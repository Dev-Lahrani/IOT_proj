#ifndef GPS_H
#define GPS_H

#include <Arduino.h>

typedef struct {
    float latitude;
    float longitude;
    bool valid;
    unsigned long last_update;
} GPSData;

class GPSReader {
public:
    GPSReader();
    void init();
    void update();
    GPSData get_data();
    void cleanup();
    
private:
    GPSData current_data;
    unsigned long last_read_time;
    
    bool parse_nmea_gprmc(const String& sentence);
    String read_line();
};

#endif // GPS_H
