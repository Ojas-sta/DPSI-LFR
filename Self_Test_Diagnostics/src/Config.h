#pragma once

// Wi-Fi Configuration
#define AP_SSID "ESP8266-Diagnostics-AP"
#define AP_PASS "" // Open Network

// System Timing
#define TELEMETRY_INTERVAL_MS 100
#define WATCHDOG_TIMEOUT_MS   500

// Motor Control Pins (Grouped sequentially using NodeMCU D-pin constants)
#define PIN_MOTOR_ENA   D6
#define PIN_MOTOR_IN1   D5
#define PIN_MOTOR_IN2   D4
#define PIN_MOTOR_IN3   D3
#define PIN_MOTOR_IN4   D2
#define PIN_MOTOR_ENB   D1
