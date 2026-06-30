#pragma once

// Wi-Fi Configuration
#define AP_SSID "ESP32-Diagnostics-AP"
#define AP_PASS "" // Open Network

// System Timing
#define TELEMETRY_INTERVAL_MS 50
#define WATCHDOG_TIMEOUT_MS   500

// Motor Control Pins (Grouped on the left side, perfectly sequential)
#define PIN_MOTOR_ENA   32
#define PIN_MOTOR_IN1   33
#define PIN_MOTOR_IN2   25
#define PIN_MOTOR_IN3   26
#define PIN_MOTOR_IN4   27
#define PIN_MOTOR_ENB   14

// PWM Configuration
#define PWM_FREQ        20000
#define PWM_RESOLUTION  8
#define LEDC_CH_LEFT    0
#define LEDC_CH_RIGHT   1

// Analog Pins (Reserved)
#define PIN_ANALOG_1    34
#define PIN_ANALOG_2    35

// I2C OLED Display
#define PIN_I2C_SDA     21
#define PIN_I2C_SCL     22
#define DISPLAY_WIDTH   128
#define DISPLAY_HEIGHT  64
