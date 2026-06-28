#include <WiFi.h>
#include <WebServer.h>

// =======================
// NETWORK SETTINGS
// =======================
const char* ssid = "MecanumRobot";
const char* password = "password123";

WebServer server(80);

// =======================
// PIN DEFINITIONS 
// (Exactly matching your screenshot)
// =======================

// --- L298N #1 (Motors 1 & 2) ---
#define M1_IN1 13
#define M1_IN2 12
#define M1_PWM 17 // ENA1

#define M2_IN1 22
#define M2_IN2 23
#define M2_PWM 16 // ENB1

// --- L298N #2 (Motor 3 ONLY - Healthy Channel) ---
#define M3_IN1 18
#define M3_IN2 5
#define M3_PWM 15 // ENA2

// --- BTS7960 Driver (Motor 4 ONLY - Replacing Fried Channel) ---
// Remember to tie L_EN and R_EN to 3.3V or 5V!
#define M4_RPWM 19 // Forward
#define M4_LPWM 21 // Backward

// Global Variables
int current_speed = 255;

// =======================
// MAIXCAM ACCOMMODATION
// =======================
// The standard hardware Serial0 (TX0=GPIO1, RX0=GPIO3) is intentionally left 
// free so that you can easily plug in the MaixCam via UART for computer vision.

// =======================
// WEB INTERFACE (HTML/JS)
// =======================
const char* html_page = R"=====(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Mecanum Control</title>
<style>
  :root {
    --bg-color: #121212;
    --panel-bg: #1e1e1e;
    --accent: #00e5ff;
    --text: #ffffff;
  }
  body {
    background-color: var(--bg-color);
    color: var(--text);
    font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
    text-align: center;
    margin: 0;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden; /* Prevents scroll bounce on mobile */
  }
  h1 { margin-bottom: 5px; font-size: 24px; color: var(--accent); text-shadow: 0 0 10px rgba(0, 229, 255, 0.5); }
  p { margin-top: 0; color: #aaa; font-size: 14px; }
  
  .card {
    background: var(--panel-bg);
    border-radius: 20px;
    padding: 20px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
  }
  
  /* Joystick Area */
  #joystick-container {
    width: 250px;
    height: 250px;
    background: radial-gradient(circle, #2a2a2a 0%, #1a1a1a 100%);
    border: 2px solid #333;
    border-radius: 50%;
    margin: 20px auto;
    position: relative;
    touch-action: none;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
  }
  
  /* The Knob */
  #joystick {
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, var(--accent) 0%, #0088aa 100%);
    border-radius: 50%;
    position: absolute;
    top: 85px; 
    left: 85px;
    pointer-events: none;
    box-shadow: 0 0 15px var(--accent);
    transition: transform 0.05s linear;
  }

  /* Slider */
  .slider-container { margin: 20px 0; }
  input[type=range] {
    -webkit-appearance: none;
    width: 100%;
    background: transparent;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    height: 25px; width: 25px;
    border-radius: 50%;
    background: var(--accent);
    cursor: pointer;
    margin-top: -10px;
    box-shadow: 0 0 10px var(--accent);
  }
  input[type=range]::-webkit-slider-runnable-track {
    width: 100%; height: 5px;
    background: #444; border-radius: 2px;
  }

  /* Button */
  .btn {
    background: #333;
    color: white;
    border: none;
    padding: 15px 20px;
    border-radius: 10px;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    font-weight: bold;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  }
  .btn.active {
    background: var(--accent);
    color: #000;
    box-shadow: 0 0 15px var(--accent);
  }
  
  /* Turnless D-Pad */
  .dpad {
    display: grid;
    grid-template-columns: repeat(3, 60px);
    gap: 10px;
    justify-content: center;
    margin: 10px 0;
  }
  .dbtn {
    width: 60px; height: 60px;
    background: #333; color: white;
    border: none; border-radius: 10px;
    font-size: 24px; cursor: pointer;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    user-select: none;
    -webkit-user-select: none;
  }
  .dbtn:active { background: var(--accent); color: black; }
</style>
</head>
<body>
  <h1>Mecanum Controller</h1>
  <p>ESP32 AP Dashboard</p>

  <div class="card">
    <p>Analog Joystick</p>
    <div id="joystick-container">
      <div id="joystick"></div>
    </div>
  </div>

  <div class="card">
    <p>Turnless D-Pad (8-Way)</p>
    <div class="dpad">
      <button class="dbtn" onmousedown="sendCmd('fl')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('fl')" ontouchend="sendCmd('stop')">↖</button>
      <button class="dbtn" onmousedown="sendCmd('f')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('f')" ontouchend="sendCmd('stop')">↑</button>
      <button class="dbtn" onmousedown="sendCmd('fr')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('fr')" ontouchend="sendCmd('stop')">↗</button>
      <button class="dbtn" onmousedown="sendCmd('l')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('l')" ontouchend="sendCmd('stop')">←</button>
      <button class="dbtn" onmousedown="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('stop')">🛑</button>
      <button class="dbtn" onmousedown="sendCmd('r')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('r')" ontouchend="sendCmd('stop')">→</button>
      <button class="dbtn" onmousedown="sendCmd('bl')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('bl')" ontouchend="sendCmd('stop')">↙</button>
      <button class="dbtn" onmousedown="sendCmd('b')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('b')" ontouchend="sendCmd('stop')">↓</button>
      <button class="dbtn" onmousedown="sendCmd('br')" onmouseup="sendCmd('stop')" ontouchstart="event.preventDefault(); sendCmd('br')" ontouchend="sendCmd('stop')">↘</button>
    </div>
  </div>

  <div class="card">
    <button id="tornadoBtn" class="btn" onclick="toggleTornado()">🌪️ Tornado Mode (Spin + Move)</button>
    
    <div class="slider-container">
      <label>Max Speed: <span id="speedVal">255</span></label>
      <input type="range" id="speed" min="0" max="255" value="255" oninput="updateSpeed(this.value)">
    </div>
  </div>

  <script>
    let jc = document.getElementById('joystick-container');
    let j = document.getElementById('joystick');
    let isDragging = false;
    let maxR = 85; 
    let vx = 0, vy = 0, vw = 0;
    let tornado = false;

    // Attach touch & mouse events
    jc.addEventListener('mousedown', startDrag);
    jc.addEventListener('touchstart', startDrag, {passive: false});
    document.addEventListener('mousemove', drag);
    document.addEventListener('touchmove', drag, {passive: false});
    document.addEventListener('mouseup', endDrag);
    document.addEventListener('touchend', endDrag);

    function startDrag(e) { 
      isDragging = true; 
      drag(e); 
    }

    function drag(e) {
      if(!isDragging) return;
      e.preventDefault();
      let rect = jc.getBoundingClientRect();
      let clientX = e.touches ? e.touches[0].clientX : e.clientX;
      let clientY = e.touches ? e.touches[0].clientY : e.clientY;
      
      let cx = rect.width / 2;
      let cy = rect.height / 2;
      let dx = clientX - rect.left - cx;
      let dy = clientY - rect.top - cy;
      
      let dist = Math.sqrt(dx*dx + dy*dy);
      if(dist > maxR) {
        dx = (dx/dist) * maxR;
        dy = (dy/dist) * maxR;
      }
      
      j.style.transform = `translate(${dx}px, ${dy}px)`;
      vx = dx / maxR;
      vy = -dy / maxR; // Invert Y so pushing UP is positive
      sendData();
    }

    function endDrag(e) {
      if(!isDragging) return;
      isDragging = false;
      j.style.transform = `translate(0px, 0px)`;
      vx = 0; vy = 0;
      sendData();
    }

    function toggleTornado() {
      tornado = !tornado;
      document.getElementById('tornadoBtn').classList.toggle('active', tornado);
      vw = tornado ? 1.0 : 0;
      sendData();
    }

    function updateSpeed(val) {
      document.getElementById('speedVal').innerText = val;
      fetch(`/speed?v=${val}`);
    }

    let lastSend = 0;
    function sendData() {
      let now = Date.now();
      if(now - lastSend < 50) return; // limit to 20 requests per second
      lastSend = now;
      fetch(`/move?x=${vx.toFixed(2)}&y=${vy.toFixed(2)}&w=${vw.toFixed(2)}`);
    }
    function sendCmd(cmd) {
      let x=0, y=0, w=0;
      if(cmd==='f') y=1;
      else if(cmd==='b') y=-1;
      else if(cmd==='l') x=-1;
      else if(cmd==='r') x=1;
      else if(cmd==='fl') { x=-1; y=1; }
      else if(cmd==='fr') { x=1; y=1; }
      else if(cmd==='bl') { x=-1; y=-1; }
      else if(cmd==='br') { x=1; y=-1; }
      fetch(`/move?x=${x}&y=${y}&w=${w}`);
    }
  </script>
</body>
</html>
)=====";

// =======================
// SETUP CODE
// =======================
void setup() {
  Serial.begin(115200);

  // Initialize motor pins
  pinMode(M1_IN1, OUTPUT); pinMode(M1_IN2, OUTPUT); pinMode(M1_PWM, OUTPUT);
  pinMode(M2_IN1, OUTPUT); pinMode(M2_IN2, OUTPUT); pinMode(M2_PWM, OUTPUT);
  pinMode(M3_IN1, OUTPUT); pinMode(M3_IN2, OUTPUT); pinMode(M3_PWM, OUTPUT); // L298N
  pinMode(M4_RPWM, OUTPUT); pinMode(M4_LPWM, OUTPUT); // BTS7960

  // Stop all motors initially
  setMotors(0, 0, 0);

  // Setup Wi-Fi AP
  WiFi.softAP(ssid, password);
  Serial.print("Access Point Started! Connect to Wi-Fi 'MecanumRobot' and visit IP: ");
  Serial.println(WiFi.softAPIP());

  // Web Server Routes
  server.on("/", []() {
    server.send(200, "text/html", html_page);
  });

  server.on("/speed", []() {
    if (server.hasArg("v")) {
      current_speed = server.arg("v").toInt();
    }
    server.send(200, "text/plain", "OK");
  });

  server.on("/move", []() {
    if (server.hasArg("x") && server.hasArg("y") && server.hasArg("w")) {
      float x = server.arg("x").toFloat();
      float y = server.arg("y").toFloat();
      float w = server.arg("w").toFloat();
      setMotors(x, y, w);
    }
    server.send(200, "text/plain", "OK");
  });

  server.begin();
}

// =======================
// MAIN LOOP
// =======================
void loop() {
  server.handleClient();

  // Serial Monitor Control (WASD)
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    // Ignore newline/carriage return characters
    if (cmd == '\n' || cmd == '\r') return;

    if (cmd == 'w' || cmd == 'W' || cmd == '8') setMotors(0, 1.0, 0);       // Forward
    else if (cmd == 's' || cmd == 'S' || cmd == '2') setMotors(0, -1.0, 0); // Backward
    else if (cmd == 'a' || cmd == 'A' || cmd == '4') setMotors(-1.0, 0, 0); // Strafe Left
    else if (cmd == 'd' || cmd == 'D' || cmd == '6') setMotors(1.0, 0, 0);  // Strafe Right
    else if (cmd == 'q' || cmd == 'Q') setMotors(0, 0, -1.0);               // Spin Left
    else if (cmd == 'e' || cmd == 'E') setMotors(0, 0, 1.0);                // Spin Right
    
    // Turnless Diagonals
    else if (cmd == '7') setMotors(-1.0, 1.0, 0); // Forward-Left
    else if (cmd == '9') setMotors(1.0, 1.0, 0);  // Forward-Right
    else if (cmd == '1') setMotors(-1.0, -1.0, 0);// Backward-Left
    else if (cmd == '3') setMotors(1.0, -1.0, 0); // Backward-Right
    
    else if (cmd == ' ' || cmd == 'x' || cmd == 'X' || cmd == '5') setMotors(0, 0, 0); // Stop
    
    Serial.print("Received Serial Command: ");
    Serial.println(cmd);
  }
}

// =======================
// MOTOR CONTROL LOGIC
// =======================
void driveMotor(int motor, float speed) {
  speed = constrain(speed, -255, 255);

  // L298N Control (Motors 1, 2, and 3)
  if (motor == 1 || motor == 2 || motor == 3) {
    int in1, in2, pwm_pin;
    if (motor == 1) { in1 = M1_IN1; in2 = M1_IN2; pwm_pin = M1_PWM; }
    if (motor == 2) { in1 = M2_IN1; in2 = M2_IN2; pwm_pin = M2_PWM; }
    if (motor == 3) { in1 = M3_IN1; in2 = M3_IN2; pwm_pin = M3_PWM; }
    
    if (speed > 0) {
      digitalWrite(in1, HIGH);
      digitalWrite(in2, LOW);
    } else if (speed < 0) {
      digitalWrite(in1, LOW);
      digitalWrite(in2, HIGH);
    } else {
      digitalWrite(in1, LOW);
      digitalWrite(in2, LOW);
    }
    analogWrite(pwm_pin, abs(speed));
  }
  
  // BTS7960 Control (Motor 4 ONLY)
  else if (motor == 4) {
    int rpwm_pin = M4_RPWM; 
    int lpwm_pin = M4_LPWM;
    
    if (speed > 0) {
      analogWrite(rpwm_pin, abs(speed));
      analogWrite(lpwm_pin, 0);
    } else if (speed < 0) {
      analogWrite(rpwm_pin, 0);
      analogWrite(lpwm_pin, abs(speed));
    } else {
      analogWrite(rpwm_pin, 0);
      analogWrite(lpwm_pin, 0);
    }
  }
}

// Calculates Mecanum wheel kinematics based on Joystick X/Y and Rotation W
void setMotors(float x, float y, float w) {
  // x = left/right translation (-1 to 1)
  // y = forward/backward translation (-1 to 1)
  // w = rotation (-1 to 1)
  
  // Kinematics for a standard Mecanum drive layout:
  // 1: Front Left, 2: Front Right, 3: Rear Left, 4: Rear Right
  float fl = y + x + w;
  float fr = y - x - w;
  float rl = y - x + w;
  float rr = y + x - w;

  // Find the highest absolute value to normalize speeds (prevents clipping)
  float max_val = abs(fl);
  if (abs(fr) > max_val) max_val = abs(fr);
  if (abs(rl) > max_val) max_val = abs(rl);
  if (abs(rr) > max_val) max_val = abs(rr);

  // Normalize all motors so the maximum is exactly 1.0
  if (max_val > 1.0) {
    fl /= max_val;
    fr /= max_val;
    rl /= max_val;
    rr /= max_val;
  }

  // Apply master speed limit and drive motors
  // If a wheel spins backwards relative to the others, swap its IN1/IN2 definitions at the top!
  driveMotor(1, fl * current_speed);
  driveMotor(2, fr * current_speed);
  driveMotor(3, rl * current_speed);
  driveMotor(4, rr * current_speed);
}
