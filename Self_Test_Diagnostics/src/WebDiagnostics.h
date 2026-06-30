#pragma once
#include <Arduino.h>
#include <ESPAsyncWebServer.h>

void initWebDiagnostics();
void processWebSocketClients();
void broadcastTelemetry(int leftPWM, int rightPWM, bool watchdogOk);
int getWebSocketClientCount();
