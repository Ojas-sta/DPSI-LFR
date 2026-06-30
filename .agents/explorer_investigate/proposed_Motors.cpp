#include "Motors.h"
#include "Config.h"

unsigned long g_last_motor_command_time = 0;
bool g_watchdog_ok = true;
int g_left_pwm = 0;
int g_right_pwm = 0;

// Global Safety & Mode Variables
bool g_armed = false;      // Default to DISARMED for safety
bool g_auto_mode = true;   // Default to AUTO mode for UART command listening

void initMotors() {
    pinMode(PIN_MOTOR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_IN2, OUTPUT);
    pinMode(PIN_MOTOR_IN3, OUTPUT);
    pinMode(PIN_MOTOR_IN4, OUTPUT);
    
    pinMode(PIN_MOTOR_ENA, OUTPUT);
    pinMode(PIN_MOTOR_ENB, OUTPUT);

    // Configure ESP8266 standard PWM
    analogWriteRange(255); // Force 8-bit resolution (0-255)
    analogWriteFreq(1000);  // Set stable 1kHz PWM frequency

    setLeftMotor(0);
    setRightMotor(0);
    feedMotorWatchdog();
}

void setLeftMotor(int speed) {
    // If not armed, force motor speed to 0 as safety override
    if (!g_armed) {
        speed = 0;
    }
    
    g_left_pwm = speed;
    if (speed == 0) {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        analogWrite(PIN_MOTOR_ENA, 0);
    } else if (speed > 0) {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, HIGH);
        analogWrite(PIN_MOTOR_ENA, constrain(speed, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        analogWrite(PIN_MOTOR_ENA, constrain(-speed, 0, 255));
    }
}

void setRightMotor(int speed) {
    // If not armed, force motor speed to 0 as safety override
    if (!g_armed) {
        speed = 0;
    }
    
    g_right_pwm = speed;
    if (speed == 0) {
        digitalWrite(PIN_MOTOR_IN3, LOW);
        digitalWrite(PIN_MOTOR_IN4, LOW);
        analogWrite(PIN_MOTOR_ENB, 0);
    } else if (speed > 0) {
        digitalWrite(PIN_MOTOR_IN3, LOW);
        digitalWrite(PIN_MOTOR_IN4, HIGH);
        analogWrite(PIN_MOTOR_ENB, constrain(speed, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_IN3, HIGH);
        digitalWrite(PIN_MOTOR_IN4, LOW);
        analogWrite(PIN_MOTOR_ENB, constrain(-speed, 0, 255));
    }
}

void feedMotorWatchdog() {
    g_last_motor_command_time = millis();
    g_watchdog_ok = true;
}

void checkMotorWatchdog() {
    if (millis() - g_last_motor_command_time > WATCHDOG_TIMEOUT_MS) {
        if (g_watchdog_ok) {
            Serial.println("[WATCHDOG] Timeout! Emergency stopping motors.");
            setLeftMotor(0);
            setRightMotor(0);
            g_watchdog_ok = false;
        }
    }
}

bool isWatchdogOk() { return g_watchdog_ok; }
int getLeftMotorPWM() { return g_left_pwm; }
int getRightMotorPWM() { return g_right_pwm; }
