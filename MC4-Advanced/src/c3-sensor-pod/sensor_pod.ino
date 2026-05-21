#include "WeMultipleLineFollower.h"

// ESP32 C3 Optimized Pins
#define SENSOR_DATA_PIN 0
#define TX_PIN 21 // Requested GPIO 21
#define RX_PIN 20 // Requested GPIO 20

WeMultipleLineFollower lineFollower(SENSOR_DATA_PIN);

void setup() {
  // Ultra-fast UART to M5 Core 2
  Serial1.begin(230400, SERIAL_8N1, RX_PIN, TX_PIN); 
  
  lineFollower.openLED();
  // No delay for minimal startup latency
}

void loop() {
  lineFollower.startRead();
  
  // Compact 5-byte packet for absolute minimum latency
  // No start byte or checksum to save bits; purely raw data stream
  Serial1.write(lineFollower.readSensor1());
  Serial1.write(lineFollower.readSensor2());
  Serial1.write(lineFollower.readSensor3());
  Serial1.write(lineFollower.readSensor4());
  Serial1.write(lineFollower.readSensor5());

  // Wait exactly enough to allow the M5 to process
  delay(5); 
}
