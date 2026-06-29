#pragma once
#include <Arduino.h>

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <title>ESP32-S3 Diagnostics</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial; text-align: center; background-color: #121212; color: #fff; margin:0; padding: 20px;}
    .card { background-color: #1e1e1e; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
    .badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; }
    .connected { background-color: #28a745; }
    .disconnected { background-color: #dc3545; }
    .ir-bar { display: flex; justify-content: center; gap: 5px; margin: 20px 0; }
    .ir-led { width: 30px; height: 30px; border-radius: 4px; background-color: #333; display: flex; align-items: center; justify-content: center; font-size: 10px; }
    .ir-on { background-color: #00ffcc; color: #000; }
    .d-pad { display: grid; grid-template-columns: 60px 60px 60px; grid-gap: 10px; justify-content: center; margin-bottom: 20px; }
    .btn { padding: 15px; font-size: 18px; cursor: pointer; border: none; border-radius: 8px; background-color: #007bff; color: white; touch-action: manipulation; }
    .btn:active { background-color: #0056b3; }
    .btn-stop { background-color: #dc3545; }
    .sliders { display: flex; justify-content: center; gap: 40px; margin-bottom: 20px; }
    .slider-container { display: flex; flex-direction: column; align-items: center; }
    #console { text-align: left; background: #000; color: #0f0; font-family: monospace; padding: 10px; height: 150px; overflow-y: auto; border-radius: 4px; }
  </style>
</head>
<body>
  <h2>ESP32-S3 Hardware Diagnostics</h2>
  <p>Status: <span id="ws-status" class="badge disconnected">Disconnected</span> | Uptime: <span id="uptime">0</span>s</p>

  <div class="card">
    <h3>10x IR Sensor Array</h3>
    <div class="ir-bar" id="ir-container">
      <!-- Generated via JS -->
    </div>
    <p>Raw Bitmask: <span id="ir-raw">0x000</span></p>
  </div>

  <div class="card">
    <h3>Motor Control Panel</h3>
    <div class="sliders">
      <div class="slider-container">
        <label>Left Speed: <span id="valL">0</span></label>
        <input type="range" id="speedL" min="-255" max="255" value="0" oninput="updateSpeed()">
      </div>
      <div class="slider-container">
        <label>Right Speed: <span id="valR">0</span></label>
        <input type="range" id="speedR" min="-255" max="255" value="0" oninput="updateSpeed()">
      </div>
    </div>
    
    <div class="d-pad">
      <div></div><button class="btn" onmousedown="drive(200, 200)" onmouseup="drive(0,0)" ontouchstart="drive(200, 200)" ontouchend="drive(0,0)">FWD</button><div></div>
      <button class="btn" onmousedown="drive(-200, 200)" onmouseup="drive(0,0)" ontouchstart="drive(-200, 200)" ontouchend="drive(0,0)">L</button>
      <button class="btn btn-stop" onclick="drive(0,0)">STOP</button>
      <button class="btn" onmousedown="drive(200, -200)" onmouseup="drive(0,0)" ontouchstart="drive(200, -200)" ontouchend="drive(0,0)">R</button>
      <div></div><button class="btn" onmousedown="drive(-200, -200)" onmouseup="drive(0,0)" ontouchstart="drive(-200, -200)" ontouchend="drive(0,0)">REV</button><div></div>
    </div>
    <p><i>Use WASD or arrow keys on keyboard.</i></p>
  </div>

  <div class="card">
    <h3>Live Console</h3>
    <div id="console"></div>
  </div>

  <script>
    const irContainer = document.getElementById('ir-container');
    for (let i = 0; i < 10; i++) {
      const div = document.createElement('div');
      div.className = 'ir-led';
      div.id = 'ir' + i;
      div.innerText = i + 1;
      irContainer.appendChild(div);
    }

    var gateway = `ws://${window.location.hostname}/ws`;
    var websocket;

    function initWebSocket() {
      websocket = new WebSocket(gateway);
      websocket.onopen    = onOpen;
      websocket.onclose   = onClose;
      websocket.onmessage = onMessage;
    }

    function onOpen(event) {
      document.getElementById('ws-status').className = 'badge connected';
      document.getElementById('ws-status').innerText = 'Connected';
      logConsole("WebSocket Connected");
    }

    function onClose(event) {
      document.getElementById('ws-status').className = 'badge disconnected';
      document.getElementById('ws-status').innerText = 'Disconnected';
      logConsole("WebSocket Disconnected. Reconnecting...");
      setTimeout(initWebSocket, 2000);
    }

    function onMessage(event) {
      const data = JSON.parse(event.data);
      if (data.type === "telemetry") {
        document.getElementById('uptime').innerText = Math.floor(data.uptime_ms / 1000);
        document.getElementById('ir-raw').innerText = "0x" + data.ir_raw.toString(16).toUpperCase();
        
        for (let i = 0; i < 10; i++) {
          const el = document.getElementById('ir' + i);
          if (data.ir_bits[i]) el.classList.add('ir-on');
          else el.classList.remove('ir-on');
        }

        if(!data.watchdog_ok) {
           logConsole("WARNING: Watchdog Triggered!");
        }
      }
    }

    function logConsole(msg) {
      const con = document.getElementById('console');
      con.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
      con.scrollTop = con.scrollHeight;
    }

    function sendCommand(left, right) {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({action: "motor", left: left, right: right}));
      }
    }

    function updateSpeed() {
      const l = parseInt(document.getElementById('speedL').value);
      const r = parseInt(document.getElementById('speedR').value);
      document.getElementById('valL').innerText = l;
      document.getElementById('valR').innerText = r;
      sendCommand(l, r);
    }

    function drive(l, r) {
      document.getElementById('speedL').value = l;
      document.getElementById('speedR').value = r;
      updateSpeed();
    }

    // Keyboard support
    document.addEventListener('keydown', (e) => {
      if(e.repeat) return;
      if(e.key === 'w' || e.key === 'ArrowUp') drive(200, 200);
      else if(e.key === 's' || e.key === 'ArrowDown') drive(-200, -200);
      else if(e.key === 'a' || e.key === 'ArrowLeft') drive(-200, 200);
      else if(e.key === 'd' || e.key === 'ArrowRight') drive(200, -200);
      else if(e.key === ' ') drive(0,0);
    });
    
    document.addEventListener('keyup', (e) => {
      if(['w','s','a','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) drive(0,0);
    });

    window.onload = initWebSocket;
  </script>
</body>
</html>
)rawliteral";
