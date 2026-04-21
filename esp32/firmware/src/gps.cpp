#include "gps.h"
#include "config.h"

HardwareSerial GPSSerial(1);

GPSReader::GPSReader() {
    current_data.latitude = FALLBACK_LATITUDE;
    current_data.longitude = FALLBACK_LONGITUDE;
    current_data.valid = false;
    current_data.last_update = 0;
    last_read_time = 0;
}

void GPSReader::init() {
    GPSSerial.begin(GPS_BAUD_RATE, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
    Serial.println("[GPS] Initialized on UART1");
}

String GPSReader::read_line() {
    String line = "";
    while (GPSSerial.available()) {
        char c = GPSSerial.read();
        if (c == '\n') {
            return line;
        }
        if (c != '\r') {
            line += c;
        }
    }
    return "";
}

bool GPSReader::parse_nmea_gprmc(const String& sentence) {
    // Format: $GPRMC,time,status,lat,N/S,lon,E/W,speed,track,date*checksum
    if (!sentence.startsWith("$GPRMC")) {
        return false;
    }
    
    int commas[12];
    int comma_idx = 0;
    for (int i = 0; i < sentence.length() && comma_idx < 12; i++) {
        if (sentence[i] == ',') {
            commas[comma_idx++] = i;
        }
    }
    
    if (comma_idx < 9) return false;
    
    // Check status (field 2)
    String status = sentence.substring(commas[1] + 1, commas[2]);
    if (status != "A") return false; // A = Active, V = Void
    
    // Parse latitude
    String lat_str = sentence.substring(commas[2] + 1, commas[3]);
    String lat_dir = sentence.substring(commas[3] + 1, commas[4]);
    if (lat_str.length() < 4) return false;
    float lat_deg = lat_str.substring(0, 2).toFloat();
    float lat_min = lat_str.substring(2).toFloat();
    current_data.latitude = lat_deg + (lat_min / 60.0f);
    if (lat_dir == "S") current_data.latitude *= -1;
    
    // Parse longitude
    String lon_str = sentence.substring(commas[4] + 1, commas[5]);
    String lon_dir = sentence.substring(commas[5] + 1, commas[6]);
    if (lon_str.length() < 5) return false;
    float lon_deg = lon_str.substring(0, 3).toFloat();
    float lon_min = lon_str.substring(3).toFloat();
    current_data.longitude = lon_deg + (lon_min / 60.0f);
    if (lon_dir == "W") current_data.longitude *= -1;
    
    current_data.valid = true;
    current_data.last_update = millis();
    return true;
}

void GPSReader::update() {
    if (millis() - last_read_time < GPS_UPDATE_INTERVAL_MS) {
        return;
    }
    
    String line = read_line();
    if (line.length() > 0) {
        if (parse_nmea_gprmc(line)) {
            Serial.printf("[GPS] Updated: %.4f, %.4f\n", 
                         current_data.latitude, current_data.longitude);
        }
    }
    
    last_read_time = millis();
}

GPSData GPSReader::get_data() {
    update();
    return current_data;
}

void GPSReader::cleanup() {
    GPSSerial.end();
    Serial.println("[GPS] Cleanup complete");
}
