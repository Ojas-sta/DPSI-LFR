#include <Arduino.h>
#include <Wire.h>
#include "M5Module4EncoderMotor.h"

// Hardware Configuration
M5Module4EncoderMotor driver;
#define MPU6886_ADDR 0x68

// Global State
uint8_t sData[5] = {0};
int32_t enc[4] = {0};
float vBat = 0;
float yaw = 0;

// Minimal MPU6886 Driver for Standalone Use
void initMPU() {
    Wire.beginTransmission(MPU6886_ADDR);
    Wire.write(0x6B); // PWR_MGMT_1
    Wire.write(0x00); // Wake up
    Wire.endTransmission();
}

void readYaw() {
    // Note: A full AHRS filter without M5Core2.h is complex. 
    // We will read raw Z-axis gyro as a placeholder for heading delta.
    Wire.beginTransmission(MPU6886_ADDR);
    Wire.write(0x47); // GYRO_ZOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6886_ADDR, 2);
    int16_t gz = (Wire.read() << 8) | Wire.read();
    yaw += (gz / 131.0) * 0.01; // Rough integration at 100Hz
}

void setup() {
    // Start standard Serial for debug
    Serial.begin(115200);
    
    // Internal I2C for IMU (Core 2 standard: SDA=21, SCL=22)
    Wire.begin(21, 22);
    initMPU();

    // Motor Module on Wire1 (Standard stacking pins 21/22 or external 32/33)
    // Using the user-provided example pinout: 21, 22
    while (!driver.begin(&Wire, MODULE_4ENCODERMOTOR_ADDR, 21, 22)) {
        Serial.println("Waiting for Motor Module...");
        delay(500);
    }

    // High-speed UART to C3 (RX=13, TX=14)
    Serial2.begin(460800, SERIAL_8N1, 13, 14);
    
    Serial.println("ULTRA-CORE STANDALONE: READY");
}

void loop() {
    // 1. Handle Serial Inputs from C3 Gateway
    if (Serial2.available() > 0 && Serial2.read() == 0xAA) {
        uint8_t type = Serial2.read();
        if (type == 0x01) { // Sensor Data
            Serial2.readBytes(sData, 5);
            Serial2.read(); // checksum skip
        } else if (type == 0x02) { // Motor Cmd
            char cmd = Serial2.read(); Serial2.read();
            int spd = 120;
            if(cmd == 'F') { driver.setMotorSpeed(0, 127+spd); driver.setMotorSpeed(2, 127-spd); }
            else if(cmd == 'B') { driver.setMotorSpeed(0, 127-spd); driver.setMotorSpeed(2, 127+spd); }
            else if(cmd == 'L') { driver.setMotorSpeed(0, 127-spd); driver.setMotorSpeed(2, 127-spd); }
            else if(cmd == 'R') { driver.setMotorSpeed(0, 127+spd); driver.setMotorSpeed(2, 127+spd); }
            else { for(int i=0; i<4; i++) driver.setMotorSpeed(i, 127); }
        }
    }

    // 2. Gather Telemetry
    for(int i=0; i<4; i++) enc[i] = driver.getEncoderValue(i);
    vBat = driver.getAnalogInput(_8bit) / 255.0 * 3.3 / 0.16;
    readYaw();

    // 3. Send Telemetry to C3 Gateway
    static unsigned long lastT = 0;
    if (millis() - lastT > 50) {
        Serial2.write(0xAA);
        Serial2.write(0x03);
        Serial2.printf("{\"s\":[%d,%d,%d,%d,%d],\"m\":[%d,%d,%d,%d],\"v\":%.1f,\"a\":%.1f}\n",
                       sData[0], sData[1], sData[2], sData[3], sData[4],
                       enc[0], enc[1], enc[2], enc[3], vBat, yaw);
        lastT = millis();
    }
    
    delay(10); // Maintain 100Hz loop
}
