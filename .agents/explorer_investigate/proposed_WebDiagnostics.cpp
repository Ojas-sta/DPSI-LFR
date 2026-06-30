#include "WebDiagnostics.h"
#include "Dashboard.h"
#include "Motors.h"
#include "Config.h"
#include <ESPAsyncTCP.h>
#include <ArduinoJson.h>

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
    if (type == WS_EVT_CONNECT) {
        Serial.printf("[WS] Client connected: %u\n", client->id());
    } else if (type == WS_EVT_DISCONNECT) {
        Serial.printf("[WS] Client disconnected: %u\n", client->id());
    } else if (type == WS_EVT_DATA) {
        AwsFrameInfo *info = (AwsFrameInfo*)arg;
        if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
            StaticJsonDocument<200> doc;
            DeserializationError err = deserializeJson(doc, data, len);
            if (!err) {
                const char* action = doc["action"];
                if (action && strcmp(action, "motor") == 0) {
                    // Only apply manual speeds if NOT in auto mode
                    if (!g_auto_mode) {
                        int left = doc["left"];
                        int right = doc["right"];
                        setLeftMotor(left);
                        setRightMotor(right);
                        feedMotorWatchdog();
                    }
                } else if (action && strcmp(action, "arm") == 0) {
                    g_armed = doc["value"];
                    if (!g_armed) {
                        setLeftMotor(0);
                        setRightMotor(0);
                    }
                    Serial.printf("[WS] Arm state updated: %s\n", g_armed ? "ARMED" : "DISARMED");
                } else if (action && strcmp(action, "mode") == 0) {
                    const char* modeStr = doc["value"];
                    if (modeStr) {
                        g_auto_mode = (strcmp(modeStr, "auto") == 0);
                    }
                    Serial.printf("[WS] Mode updated: %s\n", g_auto_mode ? "AUTO" : "MANUAL");
                }
            }
        }
    }
}

void initWebDiagnostics() {
    ws.onEvent(onEvent);
    server.addHandler(&ws);

    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send_P(200, "text/html", DASHBOARD_HTML);
    });

    server.begin();
    Serial.println("[WEB] AsyncWebServer started on port 80");
}

void processWebSocketClients() {
    ws.cleanupClients();
}

int getWebSocketClientCount() {
    return ws.count();
}

void broadcastTelemetry(int leftPWM, int rightPWM, bool watchdogOk) {
    if (ws.count() > 0) {
        StaticJsonDocument<256> doc;
        doc["type"] = "telemetry";
        doc["uptime_ms"] = millis();
        JsonObject motors = doc.createNestedObject("motors");
        motors["left"] = leftPWM;
        motors["right"] = rightPWM;
        doc["watchdog_ok"] = watchdogOk;
        doc["armed"] = g_armed;
        doc["mode"] = g_auto_mode ? "auto" : "manual";

        char buffer[256];
        size_t len = serializeJson(doc, buffer);
        ws.textAll(buffer, len);
    }
}
