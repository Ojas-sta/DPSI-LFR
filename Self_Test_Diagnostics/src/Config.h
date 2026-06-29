#pragma once
#include <Arduino.h>

// Wi-Fi Configuration
#define AP_SSID "ESP32-Diagnostics-AP"
#define AP_PASS "diagnostics123"

// Motor Pins (L298N)
#define PIN_MOTOR_L_ENA 11
#define PIN_MOTOR_L_IN1 12
#define PIN_MOTOR_L_IN2 13
#define PIN_MOTOR_R_ENB 47
#define PIN_MOTOR_R_IN3 14
#define PIN_MOTOR_R_IN4 21

// LEDC PWM Configuration
#define PWM_FREQ 20000
#define PWM_RES 8
#define PWM_CHANNEL_L 0
#define PWM_CHANNEL_R 1

// IR Sensor Array (10 sensors)
const uint8_t IR_PINS[10] = {1, 2, 4, 5, 6, 7, 15, 16, 17, 18};

// Timing Constraints
#define TELEMETRY_INTERVAL_MS 50
#define WATCHDOG_TIMEOUT_MS 500
