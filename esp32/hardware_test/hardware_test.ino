/*
 * ESP32 Controller — Hardware self-test sketch
 *
 * Runs each peripheral once in setup(), then loops the GPS reader
 * so you can keep watching NMEA output.
 *
 * Wiring (same as controller_arduino.ino):
 *   Buzzer         GPIO 12
 *   LED            GPIO 4
 *   Vibration      GPIO 2
 *   Neo-6M TX  ->  GPIO 16 (ESP32 RX1)
 *   Neo-6M RX  <-  GPIO 17 (ESP32 TX1)
 *
 * Upload (Arduino IDE):
 *   Board:         "ESP32 Dev Module"
 *   Upload speed:  921600
 *   Serial Monitor: 115200 baud
 */

#include <Arduino.h>
#include <HardwareSerial.h>

#define BUZZER_PIN       12
#define LED_PIN          4
#define VIBRATION_PIN    2

#define GPS_RX_PIN       16   // ESP32 RX1  <- GPS TX
#define GPS_TX_PIN       17   // ESP32 TX1  -> GPS RX
#define GPS_BAUD         9600

HardwareSerial GPS(1);

void testLED() {
  Serial.println(F("[1/4] LED  — 5 blinks on GPIO 4"));
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  Serial.println(F("      done."));
}

void testBuzzer() {
  Serial.println(F("[2/4] BUZZER — 3 beeps on GPIO 12"));
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(300);
    digitalWrite(BUZZER_PIN, LOW);
    delay(300);
  }
  Serial.println(F("      done."));
}

void testVibration() {
  Serial.println(F("[3/4] VIBRATION — 2 pulses on GPIO 2"));
  for (int i = 0; i < 2; i++) {
    digitalWrite(VIBRATION_PIN, HIGH);
    delay(800);
    digitalWrite(VIBRATION_PIN, LOW);
    delay(400);
  }
  Serial.println(F("      done."));
}

void testGPS() {
  Serial.println(F("[4/4] GPS — reading NMEA for 10 s (GPIO 16 RX / 17 TX)"));
  unsigned long start = millis();
  size_t bytes = 0;
  while (millis() - start < 10000) {
    while (GPS.available()) {
      int c = GPS.read();
      Serial.write(c);
      bytes++;
    }
  }
  Serial.println();
  Serial.print(F("      received "));
  Serial.print(bytes);
  Serial.println(F(" bytes."));
  if (bytes == 0) {
    Serial.println(F("      FAIL: no data. Check TX->GPIO16, RX->GPIO17, VCC, GND."));
  } else {
    Serial.println(F("      OK: data flowing. (Fix can take minutes outdoors on cold start.)"));
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(VIBRATION_PIN, LOW);

  GPS.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  Serial.println();
  Serial.println(F("==== ESP32 Controller Self-Test ===="));

  testLED();       delay(500);
  testBuzzer();    delay(500);
  testVibration(); delay(500);
  testGPS();

  Serial.println(F("==== All tests complete — streaming GPS ===="));
}

void loop() {
  while (GPS.available()) {
    Serial.write(GPS.read());
  }
}
