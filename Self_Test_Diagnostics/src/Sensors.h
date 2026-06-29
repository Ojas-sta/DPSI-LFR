#pragma once
#include <Arduino.h>

void initSensors();
uint16_t getIRRaw();
void getIRBits(uint8_t* bitsArray);
