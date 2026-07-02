# Technical Blueprint: ESP32-S3 Asynchronous Web Server & WebSocket Architecture

## 1. Architectural Overview & Design Philosophy

The diagnostic subsystem of the line-following robot (DPSI-LFR) provides real-time monitoring and low-latency manual control over a direct wireless connection. To achieve sub-20ms control responsiveness alongside a continuous 20Hz telemetry stream without degrading low-level motor control loops or sensor sampling, the architecture leverages the dual-core capability of the ESP32-S3 microcontroller running FreeRTOS alongside an asynchronous network stack.

```
+-----------------------------------------------------------------------------------+
|                                 ESP32-S3 DUAL CORE                                |
|                                                                                   |
|  CORE 0: Network & Protocol Stack              CORE 1: Control & Perception       |
|  +-------------------------------+             +-------------------------------+  |
|  | SoftAP Wi-Fi (192.168.4.1)     |             | 10x TCRT5000 Sampling (20Hz)  |  |
|  | lwIP TCP/IP Engine            |             | Bitmask & JSON Serialization |  |
|  | ESPAsyncWebServer / WebSocket |             | L298N Motor Driver (LEDC PWM) |  |
|  +---------------+---------------+             +---------------+---------------+  |
|                  |                                             |                  |
|                  |           Inter-Core FreeRTOS Queues        |                  |
|                  +=============================================+                  |
+-----------------------------------------------------------------------------------+
```

### Key Architectural Metrics
- **Wi-Fi Mode**: Standalone SoftAP (`WIFI_MODE_AP`).
- **Network Stack**: Asynchronous, non-blocking HTTP and WebSocket daemon (`ESPAsyncWebServer` + `AsyncWebSocket`).
- **Control Target**: Motor packet processing latency $< 20\text{ ms}$ end-to-end.
- **Telemetry Frequency**: 20 Hz periodic broadcast ($50\text{ ms}$ period).
- **Core Allocation**: Protocol stack isolated to Core 0; real-time sensor/motor loops dedicated to Core 1.

---

## 2. ESP32-S3 SoftAP Network Configuration

### 2.1 Wi-Fi Subsystem Initialization
The ESP32-S3 operates as a standalone Access Point (SoftAP), generating its own isolated Wi-Fi network. This guarantees connectivity in field environments independent of external infrastructure.

- **SSID**: `ESP32-S3-Diagnostics`
- **Channel**: Channel 6 (2.4 GHz spectrum selected to balance co-channel interference and propagation performance).
- **Security**: Open or WPA2-PSK (Defaulting to open for rapid diagnostic connection, configurable via `Config.h`).
- **Max Connections**: Limited to 4 simultaneous client stations to preserve memory buffers and CPU cycles on Core 0.
- **Beacon Interval**: 100 ms (Standard 802.11 beacon framing for rapid AP discovery).

### 2.2 Network Layer & IP Addressing
The embedded lwIP stack establishes a static IPv4 private network:

| Network Property | Value | Description |
| :--- | :--- | :--- |
| **Local IP (Gateway)** | `192.168.4.1` | Fixed gateway address for the ESP32-S3 SoftAP interface |
| **Subnet Mask** | `255.255.255.0` | `/24` class C subnet |
| **DHCP Server Range** | `192.168.4.2` to `192.168.4.10` | Embedded DHCP lease pool managed by lwIP |
| **DNS Server** | Disabled / Captive optional | Direct IP routing utilized for lower protocol overhead |

---

## 3. Asynchronous Web Server Core (`ESPAsyncWebServer`)

### 3.1 Non-Blocking Lifecycle
Traditional synchronous web servers (such as standard `WebServer.h`) block the CPU thread while listening for client sockets, parsing HTTP headers, and streaming payload bodies. `ESPAsyncWebServer` utilizes underlying asynchronous TCP events triggered by the hardware network interface, eliminating linear blocking loops (`server.handleClient()`).

### 3.2 Endpoint Routing Architecture
The server exposes two primary resource interfaces:

1. **Static HTML/JS UI Endpoint (`GET /`)**:
   - Serves the diagnostic dashboard compiled directly into internal PROGMEM flash memory.
   - Headers include `Content-Type: text/html` and `Cache-Control: max-age=86400` to minimize flash reads during repeated client requests.
2. **WebSocket Communication Endpoint (`ws://192.168.4.1/ws`)**:
   - Full-duplex WebSocket upgrade endpoint handling bi-directional payload transfers.

---

## 4. WebSocket Communication Layer (`AsyncWebSocket`)

### 4.1 Event Callback Architecture
The WebSocket layer operates via asynchronous event callbacks bound to the `/ws` URI path. The primary event dispatcher handles four lifecycle states:

```
                      +-------------------+
                      | WS_EVT_CONNECT    | --> Allocate Client Context / Log IP
                      +-------------------+
                      | WS_EVT_DISCONNECT | --> Clear Watchdog / Reset State
Event Dispatcher ---> +-------------------+
                      | WS_EVT_DATA       | --> Inbound Motor / Config Packets
                      +-------------------+
                      | WS_EVT_PONG       | --> Compute Round-Trip Time (RTT)
                      +-------------------+
```

- **`WS_EVT_CONNECT`**: Client socket established. The server logs the client ID and immediately schedules an initial telemetry packet to synchronize UI state.
- **`WS_EVT_DISCONNECT`**: Client disconnected. If the active controlling client disconnects, the system immediately dispatches an emergency stop signal to the motor controller.
- **`WS_EVT_DATA`**: Inbound frame received. Frame flags (`len`, `index`, `final`) are verified. Single-frame JSON payloads are parsed directly; fragmented packets are assembled in a temporary thread-safe buffer.
- **`WS_EVT_PONG`**: Heartbeat response used by the telemetry scheduler to compute current connection latency.

### 4.2 Latency & Throughput Optimization
To enforce the $<20\text{ ms}$ motor control latency and smooth $20\text{Hz}$ telemetry stream:
- **Nagle's Algorithm (`TCP_NODELAY`)**: Enabled on all active WebSocket client sockets. Disabling packet buffering at the TCP layer ensures motor commands and telemetry frames are transmitted immediately without awaiting ACK accumulators.
- **Binary vs JSON Framing**: While telemetry is JSON-formatted for web dashboard compatibility, packet size is tightly capped under 128 bytes to prevent IP fragmentation at the MAC layer.

---

## 5. FreeRTOS Task Integration & Event Loop Handling

### 5.1 Dual-Core Execution Model
To ensure network jitter does not degrade motor control or line-following accuracy, tasks are explicitly pinned to specific ESP32-S3 CPU cores:

| Task Name | Core ID | Priority | Purpose |
| :--- | :---: | :---: | :--- |
| `AsyncNetworkTask` | 0 | 3 | Manages lwIP stack callbacks, Wi-Fi drivers, and WebSocket event dispatching. |
| `MotorControlTask` | 1 | 5 | Runs high-frequency motor control loops, PWM generation, and watchdog monitoring. |
| `TelemetryTask` | 1 | 2 | Periodically samples IR array, formats bitmask, and pushes frames to network queue. |

### 5.2 Inter-Core Communication Mechanism
Passing data between Core 0 and Core 1 must be strictly non-blocking and thread-safe:
- **Inbound Control (Core 0 to Core 1)**: When a valid motor control JSON string is received in `WS_EVT_DATA` on Core 0, it is parsed and written to a lock-free atomic struct or high-priority FreeRTOS Queue (`xMotorCommandQueue`). Core 1 consumes this queue without lock contention.
- **Outbound Telemetry (Core 1 to Core 0)**: The `TelemetryTask` on Core 1 reads sensor GPIOs, formats the state, and posts the snapshot to a Ring Buffer (`xTelemetryQueue`). The `AsyncNetworkTask` on Core 0 empties this buffer and calls `ws.textAll()` during idle network cycles.

---

## 6. Memory Management & Buffer Optimization

### 6.1 Heap Protection & Allocation Strategy
Dynamic heap allocation (`malloc`, `new`, `ArduinoJson` dynamic buffers) inside high-frequency network callbacks causes heap fragmentation, leading to sudden out-of-memory (OOM) crashes in long-running embedded systems.
- **Static Allocations**: All JSON serialization and deserialization buffers utilize static stack allocation (`StaticJsonDocument<256>`).
- **Pre-Allocated Async Queues**: The `AsyncWebSocket` client buffer limit is configured to static limits (`WS_MAX_QUEUED_MESSAGES = 8`). If a slow Wi-Fi client fails to acknowledge packets, older telemetry packets are dropped rather than accumulating in dynamic RAM.

### 6.2 Heap Monitoring Metrics
The firmware implements continuous runtime diagnostics:
- `ESP.getFreeHeap()` monitored via heartbeat routines.
- `uxTaskGetStackHighWaterMark()` checked periodically to verify stack allocation boundaries for network tasks.
