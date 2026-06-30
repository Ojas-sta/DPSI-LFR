#pragma once
#include <Arduino.h>
#include <ESPAsyncWebServer.h>

void initWebDiagnostics();
void processWebSocketClients();
void broadcastTelemetry(uint16_t irBitmask, uint8_t* irBits, int leftPWM, int rightPWM, bool watchdogOk);
int getWebSocketClientCount();
