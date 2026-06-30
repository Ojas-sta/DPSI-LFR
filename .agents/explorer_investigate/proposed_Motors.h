#pragma once
#include <Arduino.h>

// Global control states
extern bool g_armed;
extern bool g_auto_mode;

void initMotors();
void setLeftMotor(int speed);
void setRightMotor(int speed);
void checkMotorWatchdog();
void feedMotorWatchdog();
bool isWatchdogOk();
int getLeftMotorPWM();
int getRightMotorPWM();
