#pragma once
#include <Arduino.h>

void initSensors();
uint16_t readIRSensorBitmask();
void getIRSensorArray(uint8_t* outArray);
