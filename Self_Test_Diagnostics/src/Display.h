#pragma once
#include <Arduino.h>

void initDisplay();
void updateDisplay(int clientCount, int leftPWM, int rightPWM, bool watchdogOk);
