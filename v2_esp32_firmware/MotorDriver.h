#ifndef MOTOR_DRIVER_H_
#define MOTOR_DRIVER_H_

#include "Config.h"

// ============================================================================
// MOTOR DRIVER INITIALIZATION
// ============================================================================

void initMotorDriver() {
    ledcAttach(PIN_MOTOR_ENA, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
    ledcAttach(PIN_MOTOR_ENB, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);

    pinMode(PIN_MOTOR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_IN2, OUTPUT);
    pinMode(PIN_MOTOR_IN3, OUTPUT);
    pinMode(PIN_MOTOR_IN4, OUTPUT);

    digitalWrite(PIN_MOTOR_IN1, LOW);
    digitalWrite(PIN_MOTOR_IN2, LOW);
    digitalWrite(PIN_MOTOR_IN3, LOW);
    digitalWrite(PIN_MOTOR_IN4, LOW);

    ledcWrite(PIN_MOTOR_ENA, 0);
    ledcWrite(PIN_MOTOR_ENB, 0);
}

// ============================================================================
// MOTOR SPEED CONTROL
// ============================================================================

void setMotorSpeeds(int16_t left_pwm, int16_t right_pwm) {
    left_pwm = constrain(left_pwm, -255, 255);
    right_pwm = constrain(right_pwm, -255, 255);

    if (left_pwm >= 0) {
        digitalWrite(PIN_MOTOR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        ledcWrite(PIN_MOTOR_ENA, left_pwm);
    } else {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, HIGH);
        ledcWrite(PIN_MOTOR_ENA, -left_pwm);
    }

    if (right_pwm >= 0) {
        digitalWrite(PIN_MOTOR_IN3, HIGH);
        digitalWrite(PIN_MOTOR_IN4, LOW);
        ledcWrite(PIN_MOTOR_ENB, right_pwm);
    } else {
        digitalWrite(PIN_MOTOR_IN3, LOW);
        digitalWrite(PIN_MOTOR_IN4, HIGH);
        ledcWrite(PIN_MOTOR_ENB, -right_pwm);
    }
}

void emergencyStopMotors() {
    ledcWrite(PIN_MOTOR_ENA, 0);
    ledcWrite(PIN_MOTOR_ENB, 0);
    digitalWrite(PIN_MOTOR_IN1, LOW);
    digitalWrite(PIN_MOTOR_IN2, LOW);
    digitalWrite(PIN_MOTOR_IN3, LOW);
    digitalWrite(PIN_MOTOR_IN4, LOW);
}

#endif // MOTOR_DRIVER_H_
