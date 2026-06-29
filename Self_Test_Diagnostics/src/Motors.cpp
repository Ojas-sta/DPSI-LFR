#include "Motors.h"
#include "Config.h"

static unsigned long last_motor_command_time = 0;
static bool watchdog_ok = true;

void initMotors() {
    pinMode(PIN_MOTOR_L_IN1, OUTPUT);
    pinMode(PIN_MOTOR_L_IN2, OUTPUT);
    pinMode(PIN_MOTOR_R_IN3, OUTPUT);
    pinMode(PIN_MOTOR_R_IN4, OUTPUT);

    // ESP32 Arduino Core v2 LEDC setup
    ledcSetup(PWM_CHANNEL_L, PWM_FREQ, PWM_RES);
    ledcAttachPin(PIN_MOTOR_L_ENA, PWM_CHANNEL_L);
    
    ledcSetup(PWM_CHANNEL_R, PWM_FREQ, PWM_RES);
    ledcAttachPin(PIN_MOTOR_R_ENB, PWM_CHANNEL_R);

    setLeftMotor(0);
    setRightMotor(0);
}

void setLeftMotor(int speed) {
    if (speed > 255) speed = 255;
    if (speed < -255) speed = -255;

    if (speed > 0) {
        digitalWrite(PIN_MOTOR_L_IN1, HIGH);
        digitalWrite(PIN_MOTOR_L_IN2, LOW);
        ledcWrite(PWM_CHANNEL_L, speed);
    } else if (speed < 0) {
        digitalWrite(PIN_MOTOR_L_IN1, LOW);
        digitalWrite(PIN_MOTOR_L_IN2, HIGH);
        ledcWrite(PWM_CHANNEL_L, -speed);
    } else {
        digitalWrite(PIN_MOTOR_L_IN1, LOW);
        digitalWrite(PIN_MOTOR_L_IN2, LOW);
        ledcWrite(PWM_CHANNEL_L, 0);
    }
}

void setRightMotor(int speed) {
    if (speed > 255) speed = 255;
    if (speed < -255) speed = -255;

    if (speed > 0) {
        digitalWrite(PIN_MOTOR_R_IN3, HIGH);
        digitalWrite(PIN_MOTOR_R_IN4, LOW);
        ledcWrite(PWM_CHANNEL_R, speed);
    } else if (speed < 0) {
        digitalWrite(PIN_MOTOR_R_IN3, LOW);
        digitalWrite(PIN_MOTOR_R_IN4, HIGH);
        ledcWrite(PWM_CHANNEL_R, -speed);
    } else {
        digitalWrite(PIN_MOTOR_R_IN3, LOW);
        digitalWrite(PIN_MOTOR_R_IN4, LOW);
        ledcWrite(PWM_CHANNEL_R, 0);
    }
}

void resetWatchdog() {
    last_motor_command_time = millis();
    if (!watchdog_ok) {
        Serial.println("[WATCHDOG] Connection restored. Watchdog OK.");
        watchdog_ok = true;
    }
}

void checkWatchdog() {
    if (watchdog_ok && (millis() - last_motor_command_time > WATCHDOG_TIMEOUT_MS)) {
        Serial.println("[WATCHDOG] TIMEOUT! Emergency Stop!");
        setLeftMotor(0);
        setRightMotor(0);
        watchdog_ok = false;
    }
}

bool isWatchdogOk() {
    return watchdog_ok;
}
