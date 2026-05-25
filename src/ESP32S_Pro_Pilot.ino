#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include "WeMultipleLineFollower.h"

// ==========================================
// 1. PIN CONFIGURATION (Derived from Clean Version)
// ==========================================

// --- L293D Motor Pins ---
const int M1_IN1 = 13; const int M1_IN2 = 12; // Front Left
const int M2_IN1 = 22; const int M2_IN2 = 23; // Front Right
const int M3_IN1 = 18; const int M3_IN2 = 5;  // Back Right
const int M4_IN1 = 19; const int M4_IN2 = 21; // Back Left

// --- Encoder Pins ---
const int ENC1_A = 25; const int ENC1_B = 26;
const int ENC2_A = 32; const int ENC2_B = 33;
const int ENC3_A = 35; const int ENC3_B = 34; // Input Only
const int ENC4_A = 4;  const int ENC4_B = 2;

// --- 20-Sensor Grid Pins (Relocated to avoid collisions) ---
#define S_ROW0 27
#define S_ROW1 14
#define S_ROW2 15
#define S_ROW3 16

// ==========================================
// 2. STATE & OBJECTS
// ==========================================
volatile long encCounts[4] = {0, 0, 0, 0};
uint8_t grid[4][5] = {0};
int motorSpeed = 200; // PWM range 0-255

WeMultipleLineFollower lf0(S_ROW0);
WeMultipleLineFollower lf1(S_ROW1);
WeMultipleLineFollower lf2(S_ROW2);
WeMultipleLineFollower lf3(S_ROW3);

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// ==========================================
// 3. INTERRUPTS
// ==========================================
void IRAM_ATTR readEnc1() { (digitalRead(ENC1_A) == digitalRead(ENC1_B)) ? encCounts[0]++ : encCounts[0]--; }
void IRAM_ATTR readEnc2() { (digitalRead(ENC2_A) == digitalRead(ENC2_B)) ? encCounts[1]++ : encCounts[1]--; }
void IRAM_ATTR readEnc3() { (digitalRead(ENC3_A) == digitalRead(ENC3_B)) ? encCounts[2]++ : encCounts[2]--; }
void IRAM_ATTR readEnc4() { (digitalRead(ENC4_A) == digitalRead(ENC4_B)) ? encCounts[3]++ : encCounts[3]--; }

// ==========================================
// 4. MOTOR CONTROL LOGIC (With PWM)
// ==========================================
void setMotor(int m, int speed) {
  int in1, in2;
  if(m==0) { in1=M1_IN1; in2=M1_IN2; }
  else if(m==1) { in1=M2_IN1; in2=M2_IN2; }
  else if(m==2) { in1=M3_IN1; in2=M3_IN2; }
  else { in1=M4_IN1; in2=M4_IN2; }

  // ESP32 supports analogWrite since Core 3.0, otherwise use ledc
  if (speed >= 0) {
    analogWrite(in1, speed);
    analogWrite(in2, 0);
  } else {
    analogWrite(in1, 0);
    analogWrite(in2, abs(speed));
  }
}

// ==========================================
// 5. WEB UI & PACKET HANDLING
// ==========================================
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<style>
    body { font-family: monospace; background: #000; color: #0f0; text-align: center; }
    .grid { display: grid; grid-template-columns: repeat(5, 30px); gap: 5px; justify-content: center; margin: 20px auto; }
    .cell { width: 30px; height: 30px; background: #111; border: 1px solid #222; }
    .on { background: #0f0; box-shadow: 0 0 10px #0f0; }
    .btn { width: 80px; height: 80px; margin: 5px; border-radius: 15px; border: 2px solid #0f0; background: none; color: #0f0; font-size: 24px; touch-action: none; }
    .btn:active { background: #0f0; color: #000; }
</style></head>
<body>
    <h2>ESP32-S PRO PILOT</h2>
    <div class="grid" id="g"></div>
    <div id="ctrl">
        <button class="btn" onpointerdown="m('F')" onpointerup="m('S')">▲</button><br>
        <button class="btn" onpointerdown="m('L')" onpointerup="m('S')">◀</button>
        <button class="btn" onclick="m('S')" style="color:red;border-color:red">■</button>
        <button class="btn" onpointerdown="m('R')" onpointerup="m('S')">▶</button><br>
        <button class="btn" onpointerdown="m('B')" onpointerup="m('S')">▼</button>
    </div>
    <script>
        let ws = new WebSocket('ws://' + window.location.hostname + '/ws');
        ws.onmessage = (e) => {
            let d = JSON.parse(e.data);
            let h = '';
            d.g.forEach(row => { row.forEach(val => { h += `<div class="cell ${val ? 'on' : ''}"></div>`; }); });
            document.getElementById('g').innerHTML = h;
        };
        function m(d) { ws.send(d); }
    </script>
</body></html>)rawliteral";

void onWsEvent(AsyncWebSocket *s, AsyncWebSocketClient *c, AwsEventType t, void *arg, uint8_t *data, size_t len) {
    if (t == WS_EVT_DATA) {
        char cmd = (char)data[0];
        int s = motorSpeed;
        if(cmd == 'F') { setMotor(0, s); setMotor(1, s); setMotor(2, s); setMotor(3, s); }
        else if(cmd == 'B') { setMotor(0, -s); setMotor(1, -s); setMotor(2, -s); setMotor(3, -s); }
        else if(cmd == 'L') { setMotor(0, -s); setMotor(1, s); setMotor(2, s); setMotor(3, -s); }
        else if(cmd == 'R') { setMotor(0, s); setMotor(1, -s); setMotor(2, -s); setMotor(3, s); }
        else { for(int i=0; i<4; i++) setMotor(i, 0); }
    }
}

// ==========================================
// 6. SETUP & LOOP
// ==========================================
void setup() {
    Serial.begin(115200);

    // Motor Pins
    int out[] = {13,12,22,23,18,5,19,21};
    for(int p : out) pinMode(p, OUTPUT);

    // Encoders
    pinMode(ENC1_A, INPUT_PULLUP); pinMode(ENC1_B, INPUT_PULLUP);
    pinMode(ENC2_A, INPUT_PULLUP); pinMode(ENC2_B, INPUT_PULLUP);
    pinMode(ENC3_A, INPUT_PULLUP); pinMode(ENC3_B, INPUT_PULLUP);
    pinMode(ENC4_A, INPUT_PULLUP); pinMode(ENC4_B, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(ENC1_A), readEnc1, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC2_A), readEnc2, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC3_A), readEnc3, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC4_A), readEnc4, CHANGE);

    // Sensors
    lf0.openLED(); lf1.openLED(); lf2.openLED(); lf3.openLED();

    // WiFi
    WiFi.softAP("ESP32S_Pro_Pilot", "password123");
    MDNS.begin("mc4");
    ws.onEvent(onWsEvent);
    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *r){ r->send_P(200, "text/html", index_html); });
    server.begin();

    Serial.println("PRO PILOT: DEPLOYED");
}

void loop() {
    // Read 4x5 Grid
    lf0.startRead(); grid[0][0]=lf0.readSensor1(); grid[0][1]=lf0.readSensor2(); grid[0][2]=lf0.readSensor3(); grid[0][3]=lf0.readSensor4(); grid[0][4]=lf0.readSensor5();
    lf1.startRead(); grid[1][0]=lf1.readSensor1(); grid[1][1]=lf1.readSensor2(); grid[1][2]=lf1.readSensor3(); grid[1][3]=lf1.readSensor4(); grid[1][4]=lf1.readSensor5();
    lf2.startRead(); grid[2][0]=lf2.readSensor1(); grid[2][1]=lf2.readSensor2(); grid[2][2]=lf2.readSensor3(); grid[2][3]=lf2.readSensor4(); grid[2][4]=lf2.readSensor5();
    lf3.startRead(); grid[3][0]=lf3.readSensor1(); grid[3][1]=lf3.readSensor2(); grid[3][2]=lf3.readSensor3(); grid[3][3]=lf3.readSensor4(); grid[3][4]=lf3.readSensor5();

    // WebSocket Update (10Hz)
    static unsigned long lastWs = 0;
    if (millis() - lastWs > 100) {
        String j = "{\"g\":[";
        for(int r=0; r<4; r++) { j+="["; for(int c=0; c<5; c++) { j+=String(grid[r][c]); if(c<4) j+=","; } j+="]"; if(r<3) j+=","; }
        j+="]}"; ws.textAll(j); lastWs = millis();
    }
    ws.cleanupClients();
    delay(5);
}
