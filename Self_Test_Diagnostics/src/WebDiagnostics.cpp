#include "WebDiagnostics.h"
#include "Dashboard.h"
#include "Motors.h"
#include "Config.h"
#include <AsyncTCP.h>
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
            data[len] = 0;
            StaticJsonDocument<200> doc;
            DeserializationError err = deserializeJson(doc, data);
            if (!err) {
                const char* action = doc["action"];
                if (action && strcmp(action, "motor") == 0) {
                    int left = doc["left"];
                    int right = doc["right"];
                    setLeftMotor(left);
                    setRightMotor(right);
                    feedMotorWatchdog();
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

        char buffer[256];
        size_t len = serializeJson(doc, buffer);
        ws.textAll(buffer, len);
    }
}
