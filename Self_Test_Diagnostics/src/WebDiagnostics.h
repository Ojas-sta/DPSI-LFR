#pragma once
#include <Arduino.h>

void initWebServer();
void broadcastTelemetry(uint16_t irRaw, uint8_t* irBits, bool watchdogOk);
void processWebSocketClients();
