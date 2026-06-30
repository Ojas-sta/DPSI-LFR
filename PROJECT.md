# Project: Line Follower Robot Two-Node Architecture Migration

## Architecture
The system consists of two primary processing nodes:
1. **Raspberry Pi Node (Vision, Stuck Detection & Competition Feedback)**:
   - Location: `/Users/roopalisingh/Downloads/TemuFollower`
   - Core files: `main.py`, `hardware.py`, `vision.py`, `feedback.py`
   - Role: Captures video, tracks black lines, detects red/green markers, queries MPU6050 IMU for stuck detection, coordinates buzzer/LED feedback, and transmits motor commands via serial UART.
2. **ESP8266 Node (Motor Actuation & Web Diagnostics Dashboard)**:
   - Location: `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`
   - Core files: `src/main.cpp`, `src/Motors.h`/`src/Motors.cpp`, `src/WebDiagnostics.h`/`src/WebDiagnostics.cpp`, `src/Dashboard.h`
   - Role: Runs a WebSocket-based diagnostics server and safety web dashboard. Listens on hardware Serial UART for motor commands, parses command floats, applies safety gates (Arm/Disarm, Auto/Manual), and drives the L298N motor driver via 8-bit PWM.

## Code Layout
- **Raspberry Pi**:
  - `hardware.py` - Hardware abstraction handling Serial UART command transmission.
  - `main.py` - Main loop coordinating vision processing, control, and feedback.
  - `vision.py` - Image processing to track lines and detect red/green indicators.
  - `feedback.py` - Orchestrates LED/buzzer animations.
- **ESP8266**:
  - `src/main.cpp` - Entry point, WiFi AP setup, WebSocket telemetry loop, and serial reading task.
  - `src/Motors.h`/`src/Motors.cpp` - Motor actuation and safety enforcement (watchdog, arming checks).
  - `src/WebDiagnostics.h`/`src/WebDiagnostics.cpp` - Server routes, WebSocket handlers, and safety override transitions.
  - `src/Dashboard.h` - HTML/JS/CSS source code for the Web Dashboard interface.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | R1: Dual-UART Pi Bridge | Refactor RPi's `hardware.py` to send clamped motor commands as `M:L,R\n` over serial `/dev/serial0` and fallback `/dev/ttyUSB0`. | None | PLANNED |
| 2 | R2: ESP8266 UART Parsing | Modify ESP8266 `main.cpp`, `Motors.h`, and `Motors.cpp` to listen to serial, scale floats by 255 to PWM, and command motors. | M1 | PLANNED |
| 3 | R3: Web Dashboard Safety & Override | Upgrade `Dashboard.h` and `WebDiagnostics.cpp` with Arm/Disarm and Auto/Manual safety toggles. Force motor outputs to 0 if disarmed. | M2 | PLANNED |
| 4 | R4: Feedback & IMU Integration | Integrate RPi `main.py`, `vision.py`, and `feedback.py` with green contour detection, synchronized tone buzzer animations, and stuck detection. | M1 | PLANNED |
| 5 | E2E System Verification | Compile ESP8266 firmware, verify syntactical correctness of Pi python files, and execute mock-based verification tests. | M3, M4 | PLANNED |

## Interface Contracts
### Raspberry Pi ↔ ESP8266 (Serial Interface)
- Format: `M:<left_speed>,<right_speed>\n`
- Bounds: `left_speed`, `right_speed` are float representations strictly clamped to `[-1.0, 1.0]`.
- Precision: 4 decimal places (e.g. `M:0.1234,-0.5678\n`).
- Frequency: Sent on control loop updates (typically 20-30Hz).

### Web Client ↔ ESP8266 (WebSocket Interface)
- JSON control frame format:
  - Arming: `{ "action": "arm", "value": true|false }`
  - Control Mode: `{ "action": "mode", "value": "auto"|"manual" }`
  - Manual Joystick Speed: `{ "action": "motor", "left": <float>, "right": <float> }`
- Telemetry broadcast format:
  - `{ "armed": true|false, "mode": "auto"|"manual", ... }`
