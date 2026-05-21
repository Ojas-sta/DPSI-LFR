#include <M5Core2.h>
#include "M5Module4EncoderMotor.h"

M5Module4EncoderMotor driver;

uint8_t sData[5] = {0};
int32_t enc[4] = {0};
float vBat = 0;
float angle = 0;

void setup() {
    M5.begin(true, false, true, true);
    M5.IMU.Init();
    while (!driver.begin(&Wire1, MODULE_4ENCODERMOTOR_ADDR, 21, 22)) delay(100);
    
    // Matched high-speed baud
    Serial2.begin(460800, SERIAL_8N1, 13, 14);
    
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setTextColor(GREEN);
    M5.Lcd.println("ULTRA-CORE: SYNCED");
}

void loop() {
    // 1. Handle Serial Inputs
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
    
    float p, r, y;
    M5.IMU.getAhrsData(&p, &r, &y);
    angle = y; // Yaw

    // 3. Send Telemetry to C3 Gateway (JSON packed for easy WS relay)
    static unsigned long lastT = 0;
    if (millis() - lastT > 50) {
        Serial2.write(0xAA);
        Serial2.write(0x03);
        Serial2.printf("{\"s\":[%d,%d,%d,%d,%d],\"m\":[%d,%d,%d,%d],\"v\":%.1f,\"a\":%.1f}\n",
                       sData[0], sData[1], sData[2], sData[3], sData[4],
                       enc[0], enc[1], enc[2], enc[3], vBat, angle);
        lastT = millis();
    }
}
