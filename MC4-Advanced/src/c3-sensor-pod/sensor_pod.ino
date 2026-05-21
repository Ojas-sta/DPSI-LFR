#include "WeMultipleLineFollower.h"
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

#define SENSOR_DATA_PIN 0
#define TX_PIN 21 
#define RX_PIN 20 

WeMultipleLineFollower lineFollower(SENSOR_DATA_PIN);
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

uint8_t sData[5] = {0};
char telemetry[128] = "{}"; // JSON cache for M5 data

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<style>
    body { font-family: 'Courier New', monospace; background: #050505; color: #0f0; text-align: center; margin: 0; }
    .container { display: flex; flex-direction: column; align-items: center; padding: 10px; }
    .grid { display: grid; grid-template-columns: repeat(5, 35px); gap: 5px; margin: 15px; }
    .cell { width: 35px; height: 35px; background: #111; border: 1px solid #222; border-radius: 3px; }
    .on { background: #0f0; box-shadow: 0 0 10px #0f0; }
    .m-box { display: flex; gap: 20px; font-size: 12px; margin-bottom: 20px; }
    .motor { border: 1px solid #333; padding: 5px; width: 60px; }
    .btn { width: 80px; height: 80px; margin: 5px; border-radius: 15px; border: 2px solid #0f0; background: none; color: #0f0; font-size: 24px; touch-action: none; cursor: pointer; }
    .btn:active { background: #0f0; color: #000; }
    #stats { font-size: 10px; color: #555; }
</style>
</head><body>
<div class="container">
    <h3>CORE-GATEWAY PRO</h3>
    <div class="grid" id="g"></div>
    <div class="m-box" id="motors"></div>
    <div id="controls">
        <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
        <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
        <button class="btn" onclick="m('S')" style="color:red;border-color:red">■</button>
        <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
        <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    </div>
    <div id="stats">LINK: SYNCING...</div>
</div>
<script>
    let ws = new WebSocket('ws://' + window.location.hostname + '/ws');
    ws.onmessage = (e) => {
        let d = JSON.parse(e.data);
        if(d.s) {
            let h = ''; for(let r=0; r<4; r++) for(let c=0; c<5; c++) h += `<div class="cell ${(d.s[c] >> r) & 1 ? 'on' : ''}"></div>`;
            document.getElementById('g').innerHTML = h;
        }
        if(d.m) {
            let mh = ''; d.m.forEach((v, i) => mh += `<div class="motor">M${i}<br>${v}</div>`);
            document.getElementById('motors').innerHTML = mh;
        }
        document.getElementById('stats').innerHTML = `IMU: ${d.a||0}° | V: ${d.v||0}V`;
    };
    function m(k) { if(ws.readyState===1) ws.send(k); }
</script>
</body></html>)rawliteral";

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
    if (type == WS_EVT_DATA) {
        Serial1.write(0xAA); Serial1.write(0x02); Serial1.write(data[0]); Serial1.write(0x02 ^ data[0]);
    }
}

void setup() {
    Serial1.begin(460800, SERIAL_8N1, RX_PIN, TX_PIN); // Even faster baud
    lineFollower.openLED();
    WiFi.softAP("MC4_ULTRA", "password123");
    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *r){ r->send_P(200, "text/html", index_html); });
    server.begin();
}

void loop() {
    lineFollower.startRead();
    sData[0] = lineFollower.readSensor1(); sData[1] = lineFollower.readSensor2();
    sData[2] = lineFollower.readSensor3(); sData[3] = lineFollower.readSensor4();
    sData[4] = lineFollower.readSensor5();

    // Send Sensors to M5
    Serial1.write(0xAA); Serial1.write(0x01); Serial1.write(sData, 5);
    uint8_t ck = 0x01 ^ sData[0] ^ sData[1] ^ sData[2] ^ sData[3] ^ sData[4];
    Serial1.write(ck);

    // Read Telemetry back from M5
    if (Serial1.available() > 0 && Serial1.read() == 0xAA) {
        if (Serial1.read() == 0x03) { // Telemetry Type
            String t = Serial1.readStringUntil('\n');
            ws.textAll(t);
        }
    }
    ws.cleanupClients();
    delay(2);
}
