#include <Arduino.h>
#include <WiFi.h>
#include "Config.h"
#include "Motors.h"
#include "Sensors.h"
#include "Display.h"
#include "WebDiagnostics.h"

unsigned long g_last_telemetry_time = 0;
unsigned long g_last_display_time = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n[SYS] Booting ESP32-S3 Diagnostics Firmware");

    // Init hardware
    initMotors();
    initSensors();
    initDisplay();

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

    // Non-blocking Watchdog check
    checkMotorWatchdog();

    // Clean up websocket clients
    processWebSocketClients();

    // Telemetry Update Loop (20Hz)
    if (current_time - g_last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        g_last_telemetry_time = current_time;

        uint16_t ir_bitmask = readIRSensorBitmask();
        uint8_t ir_bits[10];
        getIRSensorArray(ir_bits);

        broadcastTelemetry(ir_bitmask, ir_bits, getLeftMotorPWM(), getRightMotorPWM(), isWatchdogOk());
    }

    // Display Update Loop (5Hz / 200ms)
    if (current_time - g_last_display_time >= 200) {
        g_last_display_time = current_time;
        
        updateDisplay(
            getWebSocketClientCount(),
            readIRSensorBitmask(),
            getLeftMotorPWM(),
            getRightMotorPWM(),
            isWatchdogOk()
        );
    }
}
