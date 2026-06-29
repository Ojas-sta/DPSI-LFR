#include <Arduino.h>
#include "Config.h"
#include "Motors.h"
#include "Sensors.h"
#include "WebDiagnostics.h"

unsigned long lastTelemetryTime = 0;

void setup() {
    Serial.begin(115200);
    Serial.println("\n[SYS] Booting Diagnostics Firmware...");

    initMotors();
    initSensors();
    initWebServer();

    Serial.println("[SYS] Boot complete. Ready for diagnostics.");
}

void loop() {
    // 1. Maintain WebSocket Clients
    processWebSocketClients();

    // 2. Check Safety Watchdog
    checkWatchdog();

    // 3. Telemetry Stream at 20Hz (every 50ms)
    unsigned long currentMillis = millis();
    if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryTime = currentMillis;

        uint16_t irRaw = getIRRaw();
        uint8_t irBits[10];
        getIRBits(irBits);
        
        bool wdog = isWatchdogOk();

        broadcastTelemetry(irRaw, irBits, wdog);
    }
}
