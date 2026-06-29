#include "WebDiagnostics.h"
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "Dashboard.h"
#include "Config.h"
#include "Motors.h"

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
    AwsFrameInfo *info = (AwsFrameInfo*)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
        data[len] = 0;
        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, (char*)data);
        
        if (!error && doc["action"] == "motor") {
            int leftSpeed = doc["left"];
            int rightSpeed = doc["right"];
            
            setLeftMotor(leftSpeed);
            setRightMotor(rightSpeed);
            resetWatchdog();
        }
    }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type,
             void *arg, uint8_t *data, size_t len) {
    switch (type) {
        case WS_EVT_CONNECT:
            Serial.printf("[WS] Client connected: %u\n", client->id());
            break;
        case WS_EVT_DISCONNECT:
            Serial.printf("[WS] Client disconnected: %u\n", client->id());
            break;
        case WS_EVT_DATA:
            handleWebSocketMessage(arg, data, len);
            break;
        case WS_EVT_PONG:
        case WS_EVT_ERROR:
            break;
    }
}

void initWebServer() {
    Serial.println("[WIFI] Starting AP...");
    WiFi.softAP(AP_SSID, AP_PASS);
    IPAddress IP = WiFi.softAPIP();
    Serial.print("[WIFI] AP IP address: ");
    Serial.println(IP);

    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send(200, "text/html", INDEX_HTML);
    });

    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.begin();
    Serial.println("[WIFI] HTTP server started");
}

void processWebSocketClients() {
    ws.cleanupClients();
}

void broadcastTelemetry(uint16_t irRaw, uint8_t* irBits, bool watchdogOk) {
    if (ws.count() == 0) return;

    StaticJsonDocument<512> doc;
    doc["type"] = "telemetry";
    doc["uptime_ms"] = millis();
    doc["ir_raw"] = irRaw;
    
    JsonArray irArray = doc.createNestedArray("ir_bits");
    for(int i=0; i<10; i++) {
        irArray.add(irBits[i]);
    }
    
    doc["watchdog_ok"] = watchdogOk;

    String jsonString;
    serializeJson(doc, jsonString);
    ws.textAll(jsonString);
}
