#include <Arduino.h>
#include <ESP8266WiFi.h>
#include "Config.h"
#include "Motors.h"
#include "WebDiagnostics.h"

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
                        float left_val = 0.0;
                        float right_val = 0.0;
                        if (sscanf(rx_buffer + 2, "%f,%f", &left_val, &right_val) == 2) {
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
    Serial.println("\n[SYS] Booting ESP8266 NodeMCU Diagnostics Firmware (MOTORS ONLY)");

    // Init hardware
    initMotors();

    // Setup AP
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS);
    
    // Force specific IP
    IPAddress ip(192, 168, 4, 1);
    IPAddress gateway(192, 168, 4, 1);
    IPAddress subnet(255, 255, 255, 0);
    WiFi.softAPConfig(ip, gateway, subnet);

    Serial.print("[WIFI] AP Started. IP: ");
    Serial.println(WiFi.softAPIP());

    // Init Web server & WebSocket
    initWebDiagnostics();
}

void loop() {
    unsigned long current_time = millis();

    // Check for serial commands from Raspberry Pi (non-blocking)
    handleSerialInput();

    // Non-blocking Watchdog check
    checkMotorWatchdog();

    // Clean up websocket clients
    processWebSocketClients();

    // Telemetry Update Loop (20Hz)
    if (current_time - g_last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        g_last_telemetry_time = current_time;

        broadcastTelemetry(getLeftMotorPWM(), getRightMotorPWM(), isWatchdogOk());
    }
}
