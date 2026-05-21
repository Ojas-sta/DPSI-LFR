#include <M5Core2.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "M5Module4EncoderMotor.h"

M5Module4EncoderMotor driver;
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

uint8_t sensorData[5] = {0, 0, 0, 0, 0};
int motorSpeed = 120;

const char* ssid = "MC4_Pro_Control";
const char* password = "password123";

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>MC4.0 Ultra-Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <style>
        body { font-family: sans-serif; background: #000; color: #00ff00; text-align: center; margin: 0; overflow: hidden; }
        .grid { display: grid; grid-template-columns: repeat(5, 40px); gap: 8px; justify-content: center; margin: 30px auto; }
        .cell { width: 40px; height: 40px; background: #111; border: 1px solid #222; border-radius: 4px; transition: 0.05s; }
        .on { background: #00ff00; box-shadow: 0 0 15px #00ff00; border-color: #fff; }
        .btn { width: 90px; height: 90px; margin: 5px; border-radius: 15px; border: 2px solid #333; background: #111; color: #00ff00; font-size: 30px; font-weight: bold; touch-action: none; }
        .btn:active { background: #00ff00; color: #000; box-shadow: 0 0 20px #00ff00; }
        .stop { border-color: #f00; color: #f00; }
        #status { font-size: 12px; color: #555; margin-top: 10px; }
    </style>
</head>
<body>
    <h2 style="margin-top:20px;">MC4.0 COMMAND</h2>
    <div class="grid" id="g"></div>
    <div>
        <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
        <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
        <button class="btn stop" onclick="m('S')">■</button>
        <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
        <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    </div>
    <div id="status">mDNS: mc4.local | WebSocket: Connecting...</div>
    <script>
        let socket = new WebSocket('ws://' + window.location.hostname + '/ws');
        socket.onopen = () => document.getElementById('status').innerHTML = "mDNS: mc4.local | WebSocket: ACTIVE";
        socket.onmessage = (e) => {
            let s = JSON.parse(e.data).s;
            let h = '';
            for(let r=0; r<4; r++) {
                for(let c=0; c<5; c++) {
                    h += `<div class="cell ${(s[c] >> r) & 1 ? 'on' : ''}"></div>`;
                }
            }
            document.getElementById('g').innerHTML = h;
        };
        function m(d) { socket.send(d); }
    </script>
</body>
</html>)rawliteral";

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
    AwsFrameInfo *info = (AwsFrameInfo*)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
        char dir = (char)data[0];
        if(dir == 'F') { driver.setMotorSpeed(0, 127+motorSpeed); driver.setMotorSpeed(2, 127-motorSpeed); }
        else if(dir == 'B') { driver.setMotorSpeed(0, 127-motorSpeed); driver.setMotorSpeed(2, 127+motorSpeed); }
        else if(dir == 'L') { driver.setMotorSpeed(0, 127-motorSpeed); driver.setMotorSpeed(2, 127-motorSpeed); }
        else if(dir == 'R') { driver.setMotorSpeed(0, 127+motorSpeed); driver.setMotorSpeed(2, 127+motorSpeed); }
        else { for(int i=0; i<4; i++) driver.setMotorSpeed(i, 127); }
    }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
    if (type == WS_EVT_DATA) handleWebSocketMessage(arg, data, len);
}

void setup() {
    M5.begin();
    while (!driver.begin(&Wire1, MODULE_4ENCODERMOTOR_ADDR, 21, 22)) delay(100);
    
    Serial2.begin(230400, SERIAL_8N1, 13, 14);

    WiFi.softAP(ssid, password);
    
    if (MDNS.begin("mc4")) {
        MDNS.addService("http", "tcp", 80);
    }

    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send_P(200, "text/html", index_html);
    });

    server.begin();
    M5.Lcd.println("AP: mc4.local ACTIVE");
}

unsigned long lastWsUpdate = 0;
void loop() {
    if (Serial2.available() >= 5) {
        Serial2.readBytes(sensorData, 5);
        
        // Push telemetry via WebSocket every 50ms for smooth 20fps visuals
        if (millis() - lastWsUpdate > 50) {
            String json = "{\"s\":[" + String(sensorData[0]) + "," + String(sensorData[1]) + "," + 
                          String(sensorData[2]) + "," + String(sensorData[3]) + "," + String(sensorData[4]) + "]}";
            ws.textAll(json);
            lastWsUpdate = millis();
        }
    }
    ws.cleanupClients();
}
