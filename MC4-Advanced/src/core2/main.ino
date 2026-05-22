#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "WeMultipleLineFollower.h"
#include "M5Module4EncoderMotor.h"

// --- Hardware Configuration - ESP32-S NodeMCU ---
// 4 Boards x 5 Sensors = 20 Sensor Grid (4x5)
#define SENSOR_PIN_ROW0 26 
#define SENSOR_PIN_ROW1 25
#define SENSOR_PIN_ROW2 33
#define SENSOR_PIN_ROW3 32

#define I2C_SDA 21         
#define I2C_SCL 22         

// --- Objects ---
WeMultipleLineFollower lf0(SENSOR_PIN_ROW0);
WeMultipleLineFollower lf1(SENSOR_PIN_ROW1);
WeMultipleLineFollower lf2(SENSOR_PIN_ROW2);
WeMultipleLineFollower lf3(SENSOR_PIN_ROW3);

M5Module4EncoderMotor driver;
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// --- State ---
uint8_t grid[4][5] = {0}; // Full 4x5 Matrix
int motorSpeed = 120;

const char* ssid = "MC4_20Sensor_Pilot";
const char* password = "password123";

// --- Web UI (Glow-Grid Visualization) ---
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<style>
    body { font-family: sans-serif; background: #000; color: #0f0; text-align: center; margin: 0; }
    .grid-container { display: flex; flex-direction: column; align-items: center; margin-top: 30px; }
    .row { display: flex; gap: 8px; margin-bottom: 8px; }
    .cell { width: 40px; height: 40px; background: #111; border: 1px solid #222; border-radius: 4px; transition: 0.05s; }
    .on { background: #00ff00; box-shadow: 0 0 15px #00ff00; border-color: #fff; }
    .btn { width: 90px; height: 90px; margin: 5px; border-radius: 15px; border: 2px solid #333; background: #111; color: #0f0; font-size: 30px; touch-action: none; }
    .btn:active { background: #0f0; color: #000; }
</style></head>
<body>
    <h2>MC4.0 4x5 GRID SYSTEM</h2>
    <div class="grid-container" id="gridDisplay"></div>
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
            d.g.forEach(row => {
                h += '<div class="row">';
                row.forEach(val => {
                    h += `<div class="cell ${val > 0 ? 'on' : ''}"></div>`;
                });
                h += '</div>';
            });
            document.getElementById('gridDisplay').innerHTML = h;
        };
        function m(d) { if(socket.readyState===1) socket.send(d); }
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

void readFullGrid() {
    // Read Board 0 (Row 0)
    lf0.startRead();
    grid[0][0] = lf0.readSensor1(); grid[0][1] = lf0.readSensor2();
    grid[0][2] = lf0.readSensor3(); grid[0][3] = lf0.readSensor4();
    grid[0][4] = lf0.readSensor5();

    // Read Board 1 (Row 1)
    lf1.startRead();
    grid[1][0] = lf1.readSensor1(); grid[1][1] = lf1.readSensor2();
    grid[1][2] = lf1.readSensor3(); grid[1][3] = lf1.readSensor4();
    grid[1][4] = lf1.readSensor5();

    // Read Board 2 (Row 2)
    lf2.startRead();
    grid[2][0] = lf2.readSensor1(); grid[2][1] = lf2.readSensor2();
    grid[2][2] = lf2.readSensor3(); grid[2][3] = lf2.readSensor4();
    grid[2][4] = lf2.readSensor5();

    // Read Board 3 (Row 3)
    lf3.startRead();
    grid[3][0] = lf3.readSensor1(); grid[3][1] = lf3.readSensor2();
    grid[3][2] = lf3.readSensor3(); grid[3][3] = lf3.readSensor4();
    grid[3][4] = lf3.readSensor5();
}

void setup() {
    Serial.begin(115200);

    // 1. Initialize I2C for Motor Module
    Wire.begin(I2C_SDA, I2C_SCL);
    while (!driver.begin(&Wire, MODULE_4ENCODERMOTOR_ADDR, I2C_SDA, I2C_SCL)) {
        Serial.println("Waiting for Motor Module...");
        delay(500);
    }

    // 2. Initialize 4 Sensor Boards
    lf0.openLED(); lf1.openLED(); lf2.openLED(); lf3.openLED();

    // 3. Network Setup
    WiFi.softAP(ssid, password);
    MDNS.begin("mc4");
    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *r){ r->send_P(200, "text/html", index_html); });
    server.begin();
    
    Serial.println("ESP32-S 20-SENSOR PILOT: READY");
}

void loop() {
    readFullGrid();

    // Stream Full Grid via WebSocket (10Hz for stability with 20 sensors)
    static unsigned long lastWs = 0;
    if (millis() - lastWs > 100) {
        String json = "{\"g\":[";
        for(int r=0; r<4; r++) {
            json += "[";
            for(int c=0; c<5; c++) {
                json += String(grid[r][c]);
                if(c<4) json += ",";
            }
            json += "]";
            if(r<3) json += ",";
        }
        json += "]}";
        ws.textAll(json);
        lastWs = millis();
    }
    
    ws.cleanupClients();
    delay(5);
}
