#ifndef CONFIG_H_
#define CONFIG_H_

#include <Arduino.h>

// ============================================================================
// GPIO PIN ASSIGNMENTS - ESP32-S3
// ============================================================================

// IR Sensor Array (TCRT5000) - 10 Sensors
#define PIN_IR_1    1   // Far Left
#define PIN_IR_2    2
#define PIN_IR_3    4
#define PIN_IR_4    5
#define PIN_IR_5    6   // Center Left
#define PIN_IR_6    7   // Center Right
#define PIN_IR_7    15
#define PIN_IR_8    16
#define PIN_IR_9    17
#define PIN_IR_10   18  // Far Right

// L298N Motor Driver - Left Motor
#define PIN_MOTOR_ENA   13  // Left Speed PWM
#define PIN_MOTOR_IN1   12  // Left Direction A
#define PIN_MOTOR_IN2   11  // Left Direction B

// L298N Motor Driver - Right Motor
#define PIN_MOTOR_IN3   10  // Right Direction A
#define PIN_MOTOR_IN4   9   // Right Direction B
#define PIN_MOTOR_ENB   46  // Right Speed PWM

// Indicator LEDs (Rescue Arena Actions)
#define PIN_LED_GREEN   41
#define PIN_LED_RED     42

// I2C Bus (Shared: SSD1306 OLED & MPU6050 IMU)
#define PIN_I2C_SDA     38
#define PIN_I2C_SCL     39

// UART Serial Communication
#define PIN_UART_TX     43  // TXD0
#define PIN_UART_RX     44  // RXD0

// ============================================================================
// LEDC PWM CONFIGURATION
// ============================================================================
#define PWM_FREQ_HZ         20000
#define PWM_RESOLUTION_BITS 8
#define LEDC_CHANNEL_LEFT   0
#define LEDC_CHANNEL_RIGHT  1

// ============================================================================
// SERIAL COMMUNICATION
// ============================================================================
#define SERIAL_BAUD_RATE    115200

// ============================================================================
// I2C CONFIGURATION
// ============================================================================
#define I2C_FREQ_HZ         400000

// I2C Device Addresses
#define MPU6050_I2C_ADDR    0x68
#define SSD1306_I2C_ADDR    0x3C

// ============================================================================
// TIMING CONSTANTS
// ============================================================================
#define WATCHDOG_TIMEOUT_MS     500
#define PID_LOOP_PERIOD_MS      10    // 100 Hz
#define IMU_POLL_PERIOD_MS      5     // 200 Hz
#define OLED_UPDATE_PERIOD_MS   100   // 10 Hz
#define TELEMETRY_PERIOD_MS     50    // 20 Hz
#define HEARTBEAT_PERIOD_MS     200

// ============================================================================
// ROBOT PHYSICAL PARAMETERS
// ============================================================================
#define TRACK_WIDTH_M       0.140f  // 140mm between wheel centers
#define WHEEL_DIAMETER_M    0.065f  // 65mm wheel diameter
#define WHEEL_RADIUS_M      0.0325f

// ============================================================================
// PID CONTROL PARAMETERS
// ============================================================================
#define PID_KP_DEFAULT      2.5f
#define PID_KI_DEFAULT      0.01f
#define PID_KD_DEFAULT      15.0f

#define PID_OUTPUT_MIN      -255
#define PID_OUTPUT_MAX      255
#define PID_INTEGRAL_MIN    -50.0f
#define PID_INTEGRAL_MAX    50.0f

#define BASE_SPEED          150  // Base PWM for line following

// ============================================================================
// IMU PARAMETERS
// ============================================================================
#define IMU_CALIBRATION_SAMPLES 1000
#define IMU_GYRO_SCALE_250DPS   131.0f  // LSB per deg/s for ±250°/s range
#define IMU_TURN_DEADBAND_DEG   0.5f    // ±0.5° accuracy for turns
#define IMU_TURN_BRAKE_MS       20      // Brake pulse duration

// ============================================================================
// BINARY PROTOCOL OPCODES
// ============================================================================
// Pi -> ESP32 Commands
#define OPCODE_SET_MOTOR_SPEEDS   0x01
#define OPCODE_EXECUTE_TURN_90    0x02
#define OPCODE_EXECUTE_TURN_180   0x03
#define OPCODE_SET_PID_GAINS      0x04
#define OPCODE_SET_MODE           0x05
#define OPCODE_ACTION_GREEN_LED   0x06
#define OPCODE_ACTION_RED_LED     0x07
#define OPCODE_HEARTBEAT_PING     0x0A
#define OPCODE_EMERGENCY_STOP     0xFF

// ESP32 -> Pi Reports
#define OPCODE_REPORT_TELEMETRY   0x81
#define OPCODE_TURN_COMPLETE      0x82
#define OPCODE_HEARTBEAT_PONG     0x8A
#define OPCODE_ACK_COMMAND        0xFE
#define OPCODE_ERROR_REPORT       0xFF

// ============================================================================
// SYSTEM MODES
// ============================================================================
#define MODE_STANDBY        0
#define MODE_LINE_FOLLOW    1
#define MODE_MANUAL         2
#define MODE_IMU_TURN       3

// Turn Direction Constants
#define TURN_LEFT           0x01
#define TURN_RIGHT          0x02

// ============================================================================
// OLED DISPLAY CONFIGURATION
// ============================================================================
#define SCREEN_WIDTH        128
#define SCREEN_HEIGHT       64

#endif // CONFIG_H_
