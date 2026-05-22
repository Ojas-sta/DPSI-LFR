#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "WeMultipleLineFollower.h"
#include "M5Module4EncoderMotor.h"

// Hardware Configuration - ESP32 C3 Super Mini
#define SENSOR_DATA_PIN 0
#define I2C_SDA 8  // Standard C3 SDA
#define I2C_SCL 9  // Standard C3 SCL

// Objects
WeMultipleLineFollower lineFollower(SENSOR_DATA_PIN);
M5Module4EncoderMotor driver;
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// State
uint8_t sData[5] = {0};
int motorSpeed = 120;

const char* ssid = "MC4_C3_Direct";
const char* password = "password123";

// --- Web UI (High-Performance WebSocket) ---
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<style>
    body { font-family: sans-serif; background: #000; color: #0f0; text-align: center; margin: 0; }
    .grid { display: grid; grid-template-columns: repeat(5, 40px); gap: 8px; justify-content: center; margin: 20px auto; }
    .cell { width: 40px; height: 40px; background: #111; border: 1px solid #222; border-radius: 4px; }
    .on { background: #0f0; box-shadow: 0 0 15px #0f0; }
    .btn { width: 90px; height: 90px; margin: 5px; border-radius: 15px; border: 2px solid #333; background: #111; color: #0f0; font-size: 30px; touch-action: none; }
    .btn:active { background: #0f0; color: #000; }
</style></head>
<body>
    <h2>MC4.0 C3 DIRECT</h2>
    <div class="grid" id="g"></div>
    <div id="ctrl">
        <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
        <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
        <button class="btn" onclick="m('S')" style="color:red;border-color:red">■</button>
        <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
        <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    </div>
    <script>
        let socket = new WebSocket('ws://' + window.location.hostname + '/ws');
        socket.onmessage = (e) => {
            let d = JSON.parse(e.data);
            let h = '';
            for(let r=0; r<4; r++) for(let c=0; c<5; c++) h += `<div class="cell ${(d.s[c] >> r) & 1 ? 'on' : ''}"></div>`;
            document.getElementById('g').innerHTML = h;
        };
        function m(d) { socket.send(d); }
    </script>
</body></html>)rawliteral";

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
    char dir = (char)data[0];
    int s = motorSpeed;
    if(dir == 'F') { driver.setMotorSpeed(0, 127+s); driver.setMotorSpeed(2, 127-s); }
    else if(dir == 'B') { driver.setMotorSpeed(0, 127-s); driver.setMotorSpeed(2, 127+s); }
    else if(dir == 'L') { driver.setMotorSpeed(0, 127-s); driver.setMotorSpeed(2, 127-s); }
    else if(dir == 'R') { driver.setMotorSpeed(0, 127+s); driver.setMotorSpeed(2, 127+s); }
    else { for(int i=0; i<4; i++) driver.setMotorSpeed(i, 127); }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
    if (type == WS_EVT_DATA) handleWebSocketMessage(arg, data, len);
}

void setup() {
    Serial.begin(115200);

    // 1. Initialize I2C for Motor Module
    Wire.begin(I2C_SDA, I2C_SCL);
    while (!driver.begin(&Wire, MODULE_4ENCODERMOTOR_ADDR, I2C_SDA, I2C_SCL)) {
        Serial.println("Waiting for Motor Module...");
        delay(500);
    }

    // 2. Initialize Line Follower
    lineFollower.openLED();

    // 3. Network Setup
    WiFi.softAP(ssid, password);
    MDNS.begin("mc4");
    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send_P(200, "text/html", index_html);
    });
    server.begin();
    
    Serial.println("C3 CONTROLLER: ACTIVE");
}

void loop() {
    // Read Sensors
    lineFollower.startRead();
    sData[0] = lineFollower.readSensor1();
    sData[1] = lineFollower.readSensor2();
    sData[2] = lineFollower.readSensor3();
    sData[3] = lineFollower.readSensor4();
    sData[4] = lineFollower.readSensor5();

    // Stream Telemetry via WebSocket (20Hz)
    static unsigned long lastWs = 0;
    if (millis() - lastWs > 50) {
        String json = "{\"s\":[" + String(sData[0]) + "," + String(sData[1]) + "," + 
                      String(sData[2]) + "," + String(sData[3]) + "," + String(sData[4]) + "]}";
        ws.textAll(json);
        lastWs = millis();
    }
    
    ws.cleanupClients();
}
