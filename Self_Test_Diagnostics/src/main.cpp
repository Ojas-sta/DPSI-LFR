#include <Arduino.h>
#include <WiFi.h>
#include "Config.h"
#include "Motors.h"
#include "WebDiagnostics.h"

unsigned long g_last_telemetry_time = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n[SYS] Booting ESP32-S3 Diagnostics Firmware (MOTORS ONLY)");

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
