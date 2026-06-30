#pragma once

// Wi-Fi Configuration
#define AP_SSID "ESP32-Diagnostics-AP"
#define AP_PASS "" // Open Network

// System Timing
#define TELEMETRY_INTERVAL_MS 50
#define WATCHDOG_TIMEOUT_MS   500

// Motor Control Pins (Grouped on the left side)
#define PIN_MOTOR_ENA   13
#define PIN_MOTOR_IN1   12
#define PIN_MOTOR_IN2   11
#define PIN_MOTOR_IN3   10
#define PIN_MOTOR_IN4   9
#define PIN_MOTOR_ENB   46

// PWM Configuration
#define PWM_FREQ        20000
#define PWM_RESOLUTION  8
#define LEDC_CH_LEFT    0
#define LEDC_CH_RIGHT   1

// IR Sensor Array Pins
#define PIN_IR_1        1
#define PIN_IR_2        2
#define PIN_IR_3        4
#define PIN_IR_4        5
#define PIN_IR_5        6
#define PIN_IR_6        7
#define PIN_IR_7        15
#define PIN_IR_8        16
#define PIN_IR_9        17
#define PIN_IR_10       18

// I2C OLED Display
#define PIN_I2C_SDA     38
#define PIN_I2C_SCL     39
#define DISPLAY_WIDTH   128
#define DISPLAY_HEIGHT  64
