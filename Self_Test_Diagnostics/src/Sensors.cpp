#include "Sensors.h"
#include "Config.h"

void initSensors() {
    pinMode(PIN_IR_1, INPUT);
    pinMode(PIN_IR_2, INPUT);
    pinMode(PIN_IR_3, INPUT);
    pinMode(PIN_IR_4, INPUT);
    pinMode(PIN_IR_5, INPUT);
    pinMode(PIN_IR_6, INPUT);
    pinMode(PIN_IR_7, INPUT);
    pinMode(PIN_IR_8, INPUT);
    pinMode(PIN_IR_9, INPUT);
    pinMode(PIN_IR_10, INPUT);
}

uint16_t readIRSensorBitmask() {
    uint16_t bitmask = 0;
    bitmask |= (digitalRead(PIN_IR_1)  << 0);
    bitmask |= (digitalRead(PIN_IR_2)  << 1);
    bitmask |= (digitalRead(PIN_IR_3)  << 2);
    bitmask |= (digitalRead(PIN_IR_4)  << 3);
    bitmask |= (digitalRead(PIN_IR_5)  << 4);
    bitmask |= (digitalRead(PIN_IR_6)  << 5);
    bitmask |= (digitalRead(PIN_IR_7)  << 6);
    bitmask |= (digitalRead(PIN_IR_8)  << 7);
    bitmask |= (digitalRead(PIN_IR_9)  << 8);
    bitmask |= (digitalRead(PIN_IR_10) << 9);
    return bitmask;
}

void getIRSensorArray(uint8_t* outArray) {
    outArray[0] = digitalRead(PIN_IR_1);
    outArray[1] = digitalRead(PIN_IR_2);
    outArray[2] = digitalRead(PIN_IR_3);
    outArray[3] = digitalRead(PIN_IR_4);
    outArray[4] = digitalRead(PIN_IR_5);
    outArray[5] = digitalRead(PIN_IR_6);
    outArray[6] = digitalRead(PIN_IR_7);
    outArray[7] = digitalRead(PIN_IR_8);
    outArray[8] = digitalRead(PIN_IR_9);
    outArray[9] = digitalRead(PIN_IR_10);
}
