#include "WeMultipleLineFollower.h"

// ==========================================
// ESP32-S3 BREADBOARD TEST
// 15-Channel Line Follower & Dual IBT-2
// ==========================================

// --- Line Follower Pins (One-Wire Protocol) ---
#define LF_FRONT_PIN 16
#define LF_LEFT_PIN 17
#define LF_RIGHT_PIN 18

// Create 3 instances of the Line Follower
WeMultipleLineFollower lf_front(LF_FRONT_PIN);
WeMultipleLineFollower lf_left(LF_LEFT_PIN);
WeMultipleLineFollower lf_right(LF_RIGHT_PIN);

// --- Motor Pins (IBT-2) ---
#define L_RPWM 4
#define L_LPWM 5
#define R_RPWM 6
#define R_LPWM 7

// Timer for motor sweep
unsigned long lastMotorUpdate = 0;
int motorState = 0; // 0=Stop, 1=Forward, 2=Stop, 3=Backward
unsigned long lastSensorUpdate = 0;

void setup() {
  Serial.begin(115200);

  // Setup motor pins
  pinMode(L_RPWM, OUTPUT);
  pinMode(L_LPWM, OUTPUT);
  pinMode(R_RPWM, OUTPUT);
  pinMode(R_LPWM, OUTPUT);

  // Ensure motors start stopped
  stopMotors();

  Serial.println("ESP32-S3 Breadboard Test Started.");
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Fast non-blocking polling for sensors (100ms)
  if (currentMillis - lastSensorUpdate >= 100) {
    lastSensorUpdate = currentMillis;

    // Trigger read on all line follower sensors
    // Added a 2ms delay between each to prevent One-Wire electrical collisions
    lf_front.startRead();
    delay(2);
    lf_left.startRead();
    delay(2);
    lf_right.startRead();

  // 2. Print raw values formatted for Serial Plotter
  // (We print all 15 values on a single line separated by commas so the plotter graphs 15 distinct lines)
  
  // Front Array (5 sensors)
  Serial.print("F1:"); Serial.print(lf_front.readSensor1()); Serial.print(",");
  Serial.print("F2:"); Serial.print(lf_front.readSensor2()); Serial.print(",");
  Serial.print("F3:"); Serial.print(lf_front.readSensor3()); Serial.print(",");
  Serial.print("F4:"); Serial.print(lf_front.readSensor4()); Serial.print(",");
  Serial.print("F5:"); Serial.print(lf_front.readSensor5()); Serial.print(",");

  // Left Array (5 sensors)
  Serial.print("L1:"); Serial.print(lf_left.readSensor1()); Serial.print(",");
  Serial.print("L2:"); Serial.print(lf_left.readSensor2()); Serial.print(",");
  Serial.print("L3:"); Serial.print(lf_left.readSensor3()); Serial.print(",");
  Serial.print("L4:"); Serial.print(lf_left.readSensor4()); Serial.print(",");
  Serial.print("L5:"); Serial.print(lf_left.readSensor5()); Serial.print(",");

  // Right Array (5 sensors)
  Serial.print("R1:"); Serial.print(lf_right.readSensor1()); Serial.print(",");
  Serial.print("R2:"); Serial.print(lf_right.readSensor2()); Serial.print(",");
  Serial.print("R3:"); Serial.print(lf_right.readSensor3()); Serial.print(",");
  Serial.print("R4:"); Serial.print(lf_right.readSensor4()); Serial.print(",");
  Serial.print("R5:"); Serial.print(lf_right.readSensor5()); Serial.println();
  }

  // 3. Non-blocking motor test sweep
  if (currentMillis - lastMotorUpdate >= 2000) { // change state every 2 seconds
    lastMotorUpdate = currentMillis;
    motorState++;
    if (motorState > 3) motorState = 0;

    if (motorState == 0) {
      stopMotors();
    } else if (motorState == 1) {
      runForward(150); // Speed: 0 to 255
    } else if (motorState == 2) {
      stopMotors();
    } else if (motorState == 3) {
      runBackward(150); // Speed: 0 to 255
    }
  }

}

// --- Motor Control Functions ---

void stopMotors() {
  analogWrite(L_RPWM, 0);
  analogWrite(L_LPWM, 0);
  analogWrite(R_RPWM, 0);
  analogWrite(R_LPWM, 0);
}

void runForward(int speed) {
  analogWrite(L_RPWM, speed);
  analogWrite(L_LPWM, 0);
  analogWrite(R_RPWM, speed);
  analogWrite(R_LPWM, 0);
}

void runBackward(int speed) {
  analogWrite(L_RPWM, 0);
  analogWrite(L_LPWM, speed);
  analogWrite(R_RPWM, 0);
  analogWrite(R_LPWM, speed);
}
