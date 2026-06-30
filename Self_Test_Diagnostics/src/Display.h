#pragma once
#include <Arduino.h>

void initDisplay();
void updateDisplay(int clientCount, uint16_t irBitmask, int leftPWM, int rightPWM, bool watchdogOk);
