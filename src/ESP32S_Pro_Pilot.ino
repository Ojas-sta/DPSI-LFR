#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "WeMultipleLineFollower.h"

// ==========================================
// 1. FINAL OPTIMIZED PINOUT (ESP32-S NodeMCU)
// ==========================================

// --- Rotation (Outputs - Grouped Right side) ---
const int M1_IN1 = 23; const int M1_IN2 = 22; 
const int M2_IN1 = 21; const int M2_IN2 = 19; 
const int M3_IN1 = 18; const int M3_IN2 = 5;  
const int M4_IN1 = 17; const int M4_IN2 = 16; 

// --- Encoders (Inputs - Grouped Left side) ---
const int ENC1_A = 36; const int ENC1_B = 39;
const int ENC2_A = 34; const int ENC2_B = 35;
const int ENC3_A = 32; const int ENC3_B = 33;
const int ENC4_A = 25; const int ENC4_B = 26;

// --- Sensors (Safe Pins - Bottom) ---
#define S_ROW0 27
#define S_ROW1 14
#define S_ROW2 15
#define S_ROW3 4

// ==========================================
// 2. STATE & OBJECTS
// ==========================================
volatile long encCounts[4] = {0, 0, 0, 0};
uint8_t grid[4][5] = {0};
int motorSpeed = 220;

WeMultipleLineFollower row0(S_ROW0);
WeMultipleLineFollower row1(S_ROW1);
WeMultipleLineFollower row2(S_ROW2);
WeMultipleLineFollower row3(S_ROW3);

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// ==========================================
// 3. INTERRUPTS (High Speed)
// ==========================================
void IRAM_ATTR readE1() { (digitalRead(ENC1_A) == digitalRead(ENC1_B)) ? encCounts[0]++ : encCounts[0]--; }
void IRAM_ATTR readE2() { (digitalRead(ENC2_A) == digitalRead(ENC2_B)) ? encCounts[1]++ : encCounts[1]--; }
void IRAM_ATTR readE3() { (digitalRead(ENC3_A) == digitalRead(ENC3_B)) ? encCounts[2]++ : encCounts[2]--; }
void IRAM_ATTR readE4() { (digitalRead(ENC4_A) == digitalRead(ENC4_B)) ? encCounts[3]++ : encCounts[3]--; }

// ==========================================
// 4. MOTOR CORE (PWM Enabled)
// ==========================================
void setMotor(int m, int spd) {
    int i1, i2;
    if(m==0) {i1=M1_IN1; i2=M1_IN2;}
    else if(m==1) {i1=M2_IN1; i2=M2_IN2;}
    else if(m==2) {i1=M3_IN1; i2=M3_IN2;}
    else {i1=M4_IN1; i2=M4_IN2;}
    
    if(spd >= 0) { analogWrite(i1, spd); analogWrite(i2, 0); }
    else { analogWrite(i1, 0); analogWrite(i2, abs(spd)); }
}

// ==========================================
// 5. WEB ENGINE
// ==========================================
const char html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><title>MC4.0 COMMAND</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { background:#000; color:#0f0; font-family:monospace; text-align:center; }
    .g { display:grid; grid-template-columns:repeat(5,30px); gap:5px; justify-content:center; margin:20px; }
    .c { width:30px; height:30px; background:#111; border:1px solid #222; }
    .on { background:#0f0; box-shadow:0 0 10px #0f0; }
    .btn { width:80px; height:80px; background:none; border:2px solid #0f0; color:#0f0; font-size:24px; cursor:pointer; }
</style></head><body>
    <h3>ESP32-S INTEGRATED</h3><div class="g" id="grid"></div>
    <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
    <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
    <button class="btn" onclick="m('S')" style="color:red;border-color:red">■</button>
    <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
    <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    <script>
        let ws = new WebSocket('ws://' + window.location.hostname + '/ws');
        ws.onmessage = (e) => {
            let d = JSON.parse(e.data); let h = '';
            d.g.forEach(r => { r.forEach(v => { h += `<div class="c ${v?'on':''}"></div>`; }); });
            document.getElementById('grid').innerHTML = h;
        };
        function m(d) { ws.send(d); }
    </script>
</body></html>)rawliteral";

void wsEvent(AsyncWebSocket *s, AsyncWebSocketClient *cl, AwsEventType t, void *arg, uint8_t *data, size_t len) {
    if(t == WS_EVT_DATA) {
        char c = (char)data[0]; int s = motorSpeed;
        if(c=='F'){setMotor(0,s);setMotor(1,s);setMotor(2,s);setMotor(3,s);}
        else if(c=='B'){setMotor(0,-s);setMotor(1,-s);setMotor(2,-s);setMotor(3,-s);}
        else if(c=='L'){setMotor(0,-s);setMotor(1,s);setMotor(2,s);setMotor(3,-s);}
        else if(c=='R'){setMotor(0,s);setMotor(1,-s);setMotor(2,-s);setMotor(3,s);}
        else {for(int i=0;i<4;i++)setMotor(i,0);}
    }
}

// ==========================================
// 6. MAIN OPS
// ==========================================
void setup() {
    Serial.begin(115200);
    int o[] = {23,22,21,19,18,5,17,16}; for(int p:o) pinMode(p, OUTPUT);
    int i[] = {36,39,34,35,32,33,25,26}; for(int p:i) pinMode(p, INPUT_PULLUP);
    
    attachInterrupt(36, readE1, CHANGE); attachInterrupt(34, readE2, CHANGE);
    attachInterrupt(32, readE3, CHANGE); attachInterrupt(25, readE4, CHANGE);
    
    row0.openLED(); row1.openLED(); row2.openLED(); row3.openLED();
    
    WiFi.softAP("MC4_Final_Pilot", "password123");
    MDNS.begin("mc4");
    ws.onEvent(wsEvent); server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *r){ r->send_P(200, "text/html", html); });
    server.begin();
}

void loop() {
    row0.startRead(); grid[0][0]=row0.readSensor1(); grid[0][1]=row0.readSensor2(); grid[0][2]=row0.readSensor3(); grid[0][3]=row0.readSensor4(); grid[0][4]=row0.readSensor5();
    row1.startRead(); grid[1][0]=row1.readSensor1(); grid[1][1]=row1.readSensor2(); grid[1][2]=row1.readSensor3(); grid[1][3]=row1.readSensor4(); grid[1][4]=row1.readSensor5();
    row2.startRead(); grid[2][0]=row2.readSensor1(); grid[2][1]=row2.readSensor2(); grid[2][2]=row2.readSensor3(); grid[2][3]=row2.readSensor4(); grid[2][4]=row2.readSensor5();
    row3.startRead(); grid[3][0]=row3.readSensor1(); grid[3][1]=row3.readSensor2(); grid[3][2]=row3.readSensor3(); grid[3][3]=row3.readSensor4(); grid[3][4]=row3.readSensor5();

    static unsigned long last = 0;
    if(millis() - last > 80) {
        String j = "{\"g\":[";
        for(int r=0;r<4;r++){j+="[";for(int c=0;c<5;c++){j+=String(grid[r][c]);if(c<4)j+=",";}j+="]";if(r<3)j+=",";}
        j+="]}"; ws.textAll(j); last = millis();
    }
    ws.cleanupClients();
    delay(2);
}
