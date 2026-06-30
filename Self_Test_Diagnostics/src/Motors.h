#pragma once
#include <Arduino.h>

void initMotors();
void setLeftMotor(int speed);
void setRightMotor(int speed);
void checkMotorWatchdog();
void feedMotorWatchdog();
bool isWatchdogOk();
int getLeftMotorPWM();
int getRightMotorPWM();
