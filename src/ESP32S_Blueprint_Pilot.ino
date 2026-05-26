#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "WeMultipleLineFollower.h"

// ==========================================
// 1. PIN CONFIGURATION (FROM BLUEPRINT)
// ==========================================

// --- Motor Driver Pins (2x L293D) ---
const int M1_IN1 = 13; const int M1_IN2 = 12; // Front Left
const int M2_IN1 = 22; const int M2_IN2 = 23; // Front Right
const int M3_IN1 = 18; const int M3_IN2 = 5;  // Back Right
const int M4_IN1 = 19; const int M4_IN2 = 21; // Back Left

// --- Encoder Pins ---
const int ENC1_A = 25; const int ENC1_B = 26; // Front Left
const int ENC2_A = 32; const int ENC2_B = 33; // Front Right
const int ENC3_A = 35; const int ENC3_B = 34; // Back Right (Input Only)
const int ENC4_A = 4;  const int ENC4_B = 2;  // Back Left

// --- Sensor Grid (4 Boards - Non-conflicting pins) ---
#define S_ROW0 27
#define S_ROW1 14
#define S_ROW2 15
#define S_ROW3 36 // Input Only, safe for sensor read

// ==========================================
// 2. STATE & OBJECTS
// ==========================================
volatile long encoderCounts[4] = {0, 0, 0, 0};
uint8_t sensorGrid[4][5] = {0};
int baseSpeed = 200;

WeMultipleLineFollower row0(S_ROW0);
WeMultipleLineFollower row1(S_ROW1);
WeMultipleLineFollower row2(S_ROW2);
WeMultipleLineFollower row3(S_ROW3);

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// ==========================================
// 3. BLUEPRINT INTERRUPTS (Optimized)
// ==========================================
void IRAM_ATTR readEncoder1() { (digitalRead(ENC1_A) == digitalRead(ENC1_B)) ? encoderCounts[0]++ : encoderCounts[0]--; }
void IRAM_ATTR readEncoder2() { (digitalRead(ENC2_A) == digitalRead(ENC2_B)) ? encoderCounts[1]++ : encoderCounts[1]--; }
void IRAM_ATTR readEncoder3() { (digitalRead(ENC3_A) == digitalRead(ENC3_B)) ? encoderCounts[2]++ : encoderCounts[2]--; }
void IRAM_ATTR readEncoder4() { (digitalRead(ENC4_A) == digitalRead(ENC4_B)) ? encoderCounts[3]++ : encoderCounts[3]--; }

// ==========================================
// 4. MOTOR CORE (PWM Enabled)
// ==========================================
void setMotor(int motorIndex, int speed) {
    int pin1, pin2;
    switch(motorIndex) {
        case 0: pin1=M1_IN1; pin2=M1_IN2; break;
        case 1: pin1=M2_IN1; pin2=M2_IN2; break;
        case 2: pin1=M3_IN1; pin2=M3_IN2; break;
        case 3: pin1=M4_IN1; pin2=M4_IN2; break;
        default: return;
    }
    if(speed >= 0) { analogWrite(pin1, speed); analogWrite(pin2, 0); }
    else { analogWrite(pin1, 0); analogWrite(pin2, abs(speed)); }
}

// ==========================================
// 5. WEB UI (Futuristic Dashboard)
// ==========================================
const char dashboard_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><title>MC4.0 MISSION CONTROL</title>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<style>
    body { font-family: 'Courier New', monospace; background: #000; color: #0f0; text-align: center; margin: 0; }
    .grid { display: grid; grid-template-columns: repeat(5, 30px); gap: 5px; justify-content: center; margin: 20px auto; }
    .cell { width: 30px; height: 30px; background: #111; border: 1px solid #222; border-radius: 4px; }
    .on { background: #0f0; box-shadow: 0 0 10px #0f0; }
    .stats { display: flex; justify-content: space-around; font-size: 12px; margin-bottom: 20px; color: #555; }
    .btn { width: 85px; height: 85px; margin: 5px; border-radius: 12px; border: 2px solid #0f0; background: none; color: #0f0; font-size: 28px; touch-action: none; cursor: pointer; }
    .btn:active { background: #0f0; color: #000; }
</style></head>
<body>
    <h3 style="margin-top:20px;">MC4.0 COMMAND UNIT</h3>
    <div class="grid" id="sensorGrid"></div>
    <div class="stats" id="encoderStats">M1:0 | M2:0 | M3:0 | M4:0</div>
    <div id="controls">
        <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
        <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
        <button class="btn" onclick="m('S')" style="color:red;border-color:red">■</button>
        <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
        <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    </div>
    <script>
        let ws = new WebSocket('ws://' + window.location.hostname + '/ws');
        ws.onmessage = (e) => {
            let data = JSON.parse(e.data);
            if(data.g) {
                let h = '';
                data.g.forEach(row => { row.forEach(val => { h += `<div class="cell ${val ? 'on' : ''}"></div>`; }); });
                document.getElementById('sensorGrid').innerHTML = h;
            }
            if(data.e) {
                document.getElementById('encoderStats').innerHTML = `M1:${data.e[0]} | M2:${data.e[1]} | M3:${data.e[2]} | M4:${data.e[3]}`;
            }
        };
        function m(d) { if(ws.readyState===1) ws.send(d); }
    </script>
</body></html>)rawliteral";

void handleWsMsg(void *arg, uint8_t *data, size_t len) {
    char cmd = (char)data[0];
    int s = baseSpeed;
    if(cmd == 'F') { for(int i=0; i<4; i++) setMotor(i, s); }
    else if(cmd == 'B') { for(int i=0; i<4; i++) setMotor(i, -s); }
    else if(cmd == 'L') { setMotor(0, -s); setMotor(1, s); setMotor(2, s); setMotor(3, -s); }
    else if(cmd == 'R') { setMotor(0, s); setMotor(1, -s); setMotor(2, -s); setMotor(3, s); }
    else { for(int i=0; i<4; i++) setMotor(i, 0); }
}

void onEvent(AsyncWebSocket *s, AsyncWebSocketClient *c, AwsEventType t, void *arg, uint8_t *data, size_t len) {
    if (t == WS_EVT_DATA) handleWsMsg(arg, data, len);
}

// ==========================================
// 6. SETUP & EXECUTION
// ==========================================
void setup() {
    Serial.begin(115200);

    // Initial Outputs
    int out[] = {M1_IN1, M1_IN2, M2_IN1, M2_IN2, M3_IN1, M3_IN2, M4_IN1, M4_IN2};
    for(int p : out) pinMode(p, OUTPUT);

    // Encoders
    int in[] = {ENC1_A, ENC1_B, ENC2_A, ENC2_B, ENC3_A, ENC3_B, ENC4_A, ENC4_B};
    for(int p : in) pinMode(p, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(ENC1_A), readEncoder1, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC2_A), readEncoder2, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC3_A), readEncoder3, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC4_A), readEncoder4, CHANGE);

    // Line Follower Grid
    row0.openLED(); row1.openLED(); row2.openLED(); row3.openLED();

    // WiFi Access Point
    WiFi.softAP("MC4_BLUEPRINT_PILOT", "password123");
    MDNS.begin("mc4");
    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *r){ r->send_P(200, "text/html", dashboard_html); });
    server.begin();

    Serial.println("BLUEPRINT PILOT: FULL STACK READY");
}

void loop() {
    // Read 4x5 Grid Sequentially
    row0.startRead(); sensorGrid[0][0]=row0.readSensor1(); sensorGrid[0][1]=row0.readSensor2(); sensorGrid[0][2]=row0.readSensor3(); sensorGrid[0][3]=row0.readSensor4(); sensorGrid[0][4]=row0.readSensor5();
    row1.startRead(); sensorGrid[1][0]=row1.readSensor1(); sensorGrid[1][1]=row1.readSensor2(); sensorGrid[1][2]=row1.readSensor3(); sensorGrid[1][3]=row1.readSensor4(); sensorGrid[1][4]=row1.readSensor5();
    row2.startRead(); sensorGrid[2][0]=row2.readSensor1(); sensorGrid[2][1]=row2.readSensor2(); sensorGrid[2][2]=row2.readSensor3(); sensorGrid[2][3]=row2.readSensor4(); sensorGrid[2][4]=row2.readSensor5();
    row3.startRead(); sensorGrid[3][0]=row3.readSensor1(); sensorGrid[3][1]=row3.readSensor2(); sensorGrid[3][2]=row3.readSensor3(); sensorGrid[3][3]=row3.readSensor4(); sensorGrid[3][4]=row3.readSensor5();

    // Stream Grid + Encoders (10Hz)
    static unsigned long lastStream = 0;
    if (millis() - lastStream > 100) {
        String json = "{\"g\":[";
        for(int r=0; r<4; r++) { json += "["; for(int c=0; c<5; c++) { json += String(sensorGrid[r][c]); if(c<4) json += ","; } json += "]"; if(r<3) json += ","; }
        json += "],\"e\":[" + String(encoderCounts[0]) + "," + String(encoderCounts[1]) + "," + String(encoderCounts[2]) + "," + String(encoderCounts[3]) + "]}";
        ws.textAll(json);
        lastStream = millis();
    }
    
    ws.cleanupClients();
    delay(2);
}
