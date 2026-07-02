# Technical Blueprint: Diagnostic Web Dashboard UI Architecture & PROGMEM Integration

## 1. Overview & Flash Storage Strategy

The diagnostic web dashboard allows field engineers to manually control the line-following robot and inspect real-time sensor array states from any Wi-Fi-enabled device (mobile, tablet, desktop) without requiring internet access or external app installations.

To eliminate filesystem dependencies (such as SPIFFS or LittleFS) and guarantee instant access upon boot, the single-page application (SPA)—comprising HTML5 structure, CSS3 styling, and ES6 JavaScript logic—is compressed and embedded directly into the ESP32-S3 firmware flash memory using C++ `PROGMEM` string literals (`const char INDEX_HTML[] PROGMEM = R"rawliteral(...)rawliteral";`).

---

## 2. UI Layout Component Architecture & ASCII Wireframe

### 2.1 Dashboard Wireframe Diagram

```
+-----------------------------------------------------------------------------------+
|  DPSI-LFR DIAGNOSTIC DASHBOARD                     [ STATUS: CONNECTED | 14ms ]  |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  IR SENSOR ARRAY TELEMETRY (10x TCRT5000)                                         |
|  +--+  +--+  +--+  +--+  +--+  +--+  +--+  +--+  +--+  +--+                       |
|  |01|  |02|  |03|  |04|  |05|  |06|  |07|  |08|  |09|  |10|                       |
|  (  )  (  )  (  )  (  )  (● )  (● )  (  )  (  )  (  )  (  )                       |
|  FarL  L-Out L-Mid L-In  C-L   C-R   R-In  R-Mid R-Out FarR                       |
|  Raw Bitmask Value: 0x0030 (48)                                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  MANUAL MOTOR CONTROL PANEL                                                       |
|                                                                                   |
|          +------------+                         SPEED REGULATION                  |
|          |    FORWARD |                         +-------------------------------+ |
|          +------------+                         | Speed: 150 / 255              | |
|  +------------+  +------------+  +------------+ | [======|--------------------] | |
|  | PIVOT LEFT |  | HARD STOP  |  | PIVOT RIGHT| +-------------------------------+ |
|  +------------+  +------------+  +------------+                                   |
|          +------------+                                                           |
|          |    REVERSE |                                                           |
|          +------------+                                                           |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### 2.2 Functional UI Modules
1. **Connection & Latency Monitoring Badge**: Positioned at the top right header. Displays real-time WebSocket connection state (Connecting, Connected, Disconnected) with a visual status LED dot and live round-trip latency in milliseconds.
2. **10-Sensor Visual LED Status Bar**: A horizontal strip representing the 10 IR sensors (`IR1` to `IR10`). Active sensors detecting the black track line glow bright green/cyan (`●`), while sensors over white ground remain dark grey (`○`).
3. **Touch/Click D-Pad Motor Control Panel**: Ergonomic cross-layout control panel designed for dual touch-screen and desktop mouse inputs. Supports momentary press behavior (drive on press down, auto-stop on release).
4. **Speed Regulation Slider**: Range input (`0` to `255`) initialized to `150` (`BASE_SPEED`), dynamically adjusting the PWM target sent in drive packets.

---

## 3. PROGMEM HTML/CSS Embedded Specification

### 3.1 Design Tokens & CSS Styling Model
The UI utilizes a dark diagnostic aesthetic with high contrast for outdoor readability.

```css
:root {
  --bg-color: #121212;
  --panel-bg: #1e1e1e;
  --accent-blue: #007bff;
  --sensor-active: #00ffcc;
  --sensor-inactive: #333333;
  --stop-red: #dc3545;
  --text-primary: #ffffff;
  --text-secondary: #aaaaaa;
}
```

### 3.2 Responsive Grid & Mobile Optimization
- **Viewport Meta**: `<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">` prevents unwanted mobile zooming during rapid multi-touch D-Pad interactions.
- **Flexbox & CSS Grid**: Sensory bars use CSS flexbox for uniform spacing across various mobile screen widths.

---

## 4. Frontend JavaScript WebSocket Architecture

### 4.1 Client Connection Lifecycle & Auto-Reconnect Logic
The frontend JavaScript initializes a WebSocket connection to `ws://${window.location.hostname}/ws`. An automated reconnect loop recovers from Wi-Fi drops.

```javascript
let websocket;
let pingInterval;
let lastPingTime;

function initWebSocket() {
  const wsUri = `ws://${window.location.hostname}/ws`;
  websocket = new WebSocket(wsUri);
  
  websocket.onopen = function(evt) {
    updateStatusBadge(true, "CONNECTED");
    startPingLoop();
  };
  
  websocket.onclose = function(evt) {
    updateStatusBadge(false, "DISCONNECTED");
    stopPingLoop();
    setTimeout(initWebSocket, 2000); // Reconnect attempt every 2s
  };
  
  websocket.onmessage = function(evt) {
    handleServerMessage(evt.data);
  };
}
```

### 4.2 Telemetry Parsing & UI Rendering
When a JSON payload containing `"type": "telemetry"` arrives, the client decodes the sensor array and updates the DOM elements efficiently without triggering full page reflows.

```javascript
function handleServerMessage(jsonString) {
  try {
    const msg = JSON.parse(jsonString);
    if (msg.type === "telemetry") {
      renderSensors(msg.sensors);
      document.getElementById("bitmask-val").innerText = 
        `0x${msg.bitmask.toString(16).toUpperCase().padStart(4, '0')} (${msg.bitmask})`;
    } else if (msg.type === "pong") {
      const rtt = Date.now() - lastPingTime;
      document.getElementById("latency-val").innerText = `${rtt}ms`;
    }
  } catch (e) {
    console.error("Malformed JSON frame", e);
  }
}

function renderSensors(sensorArray) {
  for (let i = 0; i < 10; i++) {
    const el = document.getElementById(`sensor-led-${i+1}`);
    if (el) {
      if (sensorArray[i] === 1) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    }
  }
}
```

### 4.3 Outbound Motor Control Event Handling
To ensure high responsiveness and zero latency lag, control commands bind to both `mousedown`/`mouseup` and `touchstart`/`touchend` events.

```javascript
let currentSpeed = 150;

function sendCommand(dir) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    const payload = JSON.stringify({
      cmd: dir,
      speed: parseInt(currentSpeed)
    });
    websocket.send(payload);
  }
}

function attachDPadListeners() {
  const bindBtn = (id, dirCommand) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    
    const startDrive = (e) => {
      e.preventDefault();
      sendCommand(dirCommand);
    };
    const stopDrive = (e) => {
      e.preventDefault();
      sendCommand("HARD_STOP");
    };
    
    btn.addEventListener("mousedown", startDrive);
    btn.addEventListener("mouseup", stopDrive);
    btn.addEventListener("touchstart", startDrive);
    btn.addEventListener("touchend", stopDrive);
  };
  
  bindBtn("btn-fwd", "FORWARD");
  bindBtn("btn-rev", "REVERSE");
  bindBtn("btn-pivot-left", "PIVOT_LEFT");
  bindBtn("btn-pivot-right", "PIVOT_RIGHT");
  bindBtn("btn-stop", "HARD_STOP");
}
```

### 4.4 Connection Heartbeat & Latency Calculation
A periodic ping frame (`{"type":"ping"}`) is dispatched every 1000ms. The server replies with a pong frame, allowing the client to measure network RTT:

$$\text{RTT} = t_{\text{receive\_pong}} - t_{\text{send\_ping}}$$
This measurement is rendered directly inside the status badge, giving operator feedback on Wi-Fi link quality.
