#include "Motors.h"
#include "Config.h"

unsigned long g_last_motor_command_time = 0;
bool g_watchdog_ok = true;
int g_left_pwm = 0;
int g_right_pwm = 0;

void initMotors() {
    pinMode(PIN_MOTOR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_IN2, OUTPUT);
    pinMode(PIN_MOTOR_IN3, OUTPUT);
    pinMode(PIN_MOTOR_IN4, OUTPUT);

    // Setup LEDC PWM Channels
    ledcSetup(LEDC_CH_LEFT, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_ENA, LEDC_CH_LEFT);
    
    ledcSetup(LEDC_CH_RIGHT, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_ENB, LEDC_CH_RIGHT);

    setLeftMotor(0);
    setRightMotor(0);
    feedMotorWatchdog();
}

void setLeftMotor(int speed) {
    g_left_pwm = speed;
    if (speed == 0) {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        ledcWrite(LEDC_CH_LEFT, 0);
    } else if (speed > 0) {
        digitalWrite(PIN_MOTOR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        ledcWrite(LEDC_CH_LEFT, constrain(speed, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, HIGH);
        ledcWrite(LEDC_CH_LEFT, constrain(-speed, 0, 255));
    }
}

void setRightMotor(int speed) {
    g_right_pwm = speed;
    if (speed == 0) {
        digitalWrite(PIN_MOTOR_IN3, LOW);
        digitalWrite(PIN_MOTOR_IN4, LOW);
        ledcWrite(LEDC_CH_RIGHT, 0);
    } else if (speed > 0) {
        digitalWrite(PIN_MOTOR_IN3, HIGH);
        digitalWrite(PIN_MOTOR_IN4, LOW);
        ledcWrite(LEDC_CH_RIGHT, constrain(speed, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_IN3, LOW);
        digitalWrite(PIN_MOTOR_IN4, HIGH);
        ledcWrite(LEDC_CH_RIGHT, constrain(-speed, 0, 255));
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
