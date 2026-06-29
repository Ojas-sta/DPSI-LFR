#pragma once
#include <Arduino.h>

void initMotors();
void setLeftMotor(int speed);
void setRightMotor(int speed);
void resetWatchdog();
void checkWatchdog();
bool isWatchdogOk();
