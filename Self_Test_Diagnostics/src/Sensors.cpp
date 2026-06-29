#include "Sensors.h"
#include "Config.h"

void initSensors() {
    for (int i = 0; i < 10; i++) {
        pinMode(IR_PINS[i], INPUT);
    }
}

uint16_t getIRRaw() {
    uint16_t bitmask = 0;
    for (int i = 0; i < 10; i++) {
        if (digitalRead(IR_PINS[i]) == HIGH) { // Assuming HIGH is line detection
            bitmask |= (1 << i);
        }
    }
    return bitmask;
}

void getIRBits(uint8_t* bitsArray) {
    for (int i = 0; i < 10; i++) {
        bitsArray[i] = digitalRead(IR_PINS[i]);
    }
}
