#include <Arduino.h>
#include <stdlib.h>
#include "Config.h"
#include "Motors.h"

unsigned long g_last_telemetry_time = 0;

// Read and parse serial input from Raspberry Pi (non-blocking)
void handleSerialInput() {
    static char rx_buffer[32];
    static int rx_index = 0;
    
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (rx_index > 0) {
                rx_buffer[rx_index] = '\0';
                
                // Parse commands like: M:<left>,<right>\n
                if (strncmp(rx_buffer, "M:", 2) == 0) {
                    // Only process UART commands if the system is in AUTO mode
                    if (g_auto_mode) {
                        char *separator = strchr(rx_buffer + 2, ',');
                        if (separator != nullptr) {
                            *separator = '\0';
                            float left_val = atof(rx_buffer + 2);
                            float right_val = atof(separator + 1);

                            // Map range -1.0..1.0 to -255..255 by multiplying by exactly 255
                            int left_pwm = (int)(left_val * 255.0f);
                            int right_pwm = (int)(right_val * 255.0f);
                            
                            // Clamp values to ensure safe range
                            left_pwm = constrain(left_pwm, -255, 255);
                            right_pwm = constrain(right_pwm, -255, 255);
                            
                            setLeftMotor(left_pwm);
                            setRightMotor(right_pwm);
                            feedMotorWatchdog();
                        }
                    }
                } else if (strncmp(rx_buffer, "A:", 2) == 0) {
                    int arm_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &arm_val) == 1) {
                        g_armed = (arm_val != 0);
                        if (!g_armed) {
                            setLeftMotor(0);
                            setRightMotor(0);
                        }
                    }
                } else if (strncmp(rx_buffer, "C:", 2) == 0) {
                    int mode_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &mode_val) == 1) {
                        g_auto_mode = (mode_val != 0);
                    }
                } else if (strcmp(rx_buffer, "P") == 0) {
                    Serial.print("P_ACK\n");
                }
                rx_index = 0;
            }
        } else if (rx_index < (int)sizeof(rx_buffer) - 1) {
            rx_buffer[rx_index++] = c;
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n[SYS] Booting Arduino Uno Diagnostics Firmware (SERIAL MOTOR CONTROL)");

    // Init hardware
    initMotors();
}

void loop() {
    unsigned long current_time = millis();

    // Check for serial commands from Raspberry Pi (non-blocking)
    handleSerialInput();

    // Non-blocking Watchdog check
    checkMotorWatchdog();

    // Serial telemetry update loop.
    if (current_time - g_last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        g_last_telemetry_time = current_time;
        Serial.print("T:");
        Serial.print(current_time);
        Serial.print(",");
        Serial.print(getLeftMotorPWM());
        Serial.print(",");
        Serial.print(getRightMotorPWM());
        Serial.print(",");
        Serial.print(isWatchdogOk() ? 1 : 0);
        Serial.print(",");
        Serial.print(g_armed ? 1 : 0);
        Serial.print(",");
        Serial.println(g_auto_mode ? 1 : 0);
    }
}
