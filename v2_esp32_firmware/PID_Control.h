#ifndef PID_CONTROL_H_
#define PID_CONTROL_H_

#include "Config.h"

// ============================================================================
// PID GAINS STRUCTURE
// ============================================================================
struct PIDGains {
    float kp;
    float ki;
    float kd;
};

// ============================================================================
// SENSOR WEIGHTS FOR LINE POSITION CALCULATION
// ============================================================================
static const int8_t sensor_weights[10] = {-9, -7, -5, -3, -1, 1, 3, 5, 7, 9};

// ============================================================================
// PID STATE VARIABLES
// ============================================================================
static float pid_integral = 0.0f;
static float pid_previous_error = 0.0f;

// ============================================================================
// FUNCTION DECLARATIONS
// ============================================================================

void initLineSensors() {
    pinMode(PIN_IR_1, INPUT_PULLUP);
    pinMode(PIN_IR_2, INPUT_PULLUP);
    pinMode(PIN_IR_3, INPUT_PULLUP);
    pinMode(PIN_IR_4, INPUT_PULLUP);
    pinMode(PIN_IR_5, INPUT_PULLUP);
    pinMode(PIN_IR_6, INPUT_PULLUP);
    pinMode(PIN_IR_7, INPUT_PULLUP);
    pinMode(PIN_IR_8, INPUT_PULLUP);
    pinMode(PIN_IR_9, INPUT_PULLUP);
    pinMode(PIN_IR_10, INPUT_PULLUP);
}

uint16_t readIRSensorBitmask() {
    uint16_t bitmask = 0;

    bitmask |= (digitalRead(PIN_IR_1) == LOW ? 1 : 0) << 9;
    bitmask |= (digitalRead(PIN_IR_2) == LOW ? 1 : 0) << 8;
    bitmask |= (digitalRead(PIN_IR_3) == LOW ? 1 : 0) << 7;
    bitmask |= (digitalRead(PIN_IR_4) == LOW ? 1 : 0) << 6;
    bitmask |= (digitalRead(PIN_IR_5) == LOW ? 1 : 0) << 5;
    bitmask |= (digitalRead(PIN_IR_6) == LOW ? 1 : 0) << 4;
    bitmask |= (digitalRead(PIN_IR_7) == LOW ? 1 : 0) << 3;
    bitmask |= (digitalRead(PIN_IR_8) == LOW ? 1 : 0) << 2;
    bitmask |= (digitalRead(PIN_IR_9) == LOW ? 1 : 0) << 1;
    bitmask |= (digitalRead(PIN_IR_10) == LOW ? 1 : 0) << 0;

    return bitmask;
}

float calculateLineError(uint16_t bitmask, float& last_error) {
    int32_t weighted_sum = 0;
    int32_t sensor_count = 0;

    for (int i = 0; i < 10; i++) {
        if (bitmask & (1 << (9 - i))) {
            weighted_sum += sensor_weights[i];
            sensor_count++;
        }
    }

    if (sensor_count == 0) {
        return (last_error >= 0.0f) ? 12.0f : -12.0f;
    }

    float error = (float)weighted_sum / (float)sensor_count;
    last_error = error;
    return error;
}

int16_t computePID(float error, PIDGains gains, float dt) {
    float P = gains.kp * error;

    pid_integral += gains.ki * error * dt;
    if (pid_integral > PID_INTEGRAL_MAX) pid_integral = PID_INTEGRAL_MAX;
    if (pid_integral < PID_INTEGRAL_MIN) pid_integral = PID_INTEGRAL_MIN;
    float I = pid_integral;

    float D = gains.kd * (error - pid_previous_error) / dt;
    pid_previous_error = error;

    float output = P + I + D;

    if (output > PID_OUTPUT_MAX) output = PID_OUTPUT_MAX;
    if (output < PID_OUTPUT_MIN) output = PID_OUTPUT_MIN;

    return (int16_t)output;
}

void resetPIDState() {
    pid_integral = 0.0f;
    pid_previous_error = 0.0f;
}

#endif // PID_CONTROL_H_
