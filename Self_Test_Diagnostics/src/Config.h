#pragma once

// System Timing
#define TELEMETRY_INTERVAL_MS 100
#define WATCHDOG_TIMEOUT_MS   500

// Arduino Uno motor control pins for an L298N-style dual motor driver.
// Pins 0/1 are reserved for hardware Serial.
#define PIN_MOTOR_ENA   5
#define PIN_MOTOR_IN1   7
#define PIN_MOTOR_IN2   8
#define PIN_MOTOR_IN3   9
#define PIN_MOTOR_IN4   10
#define PIN_MOTOR_ENB   6
