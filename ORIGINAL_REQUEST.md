# Original User Request

## Initial Request — 2026-06-30T17:30:40+05:30

/goal

Migrate a Line Follower robot to a two-node architecture: a Raspberry Pi handling vision/metrics and sending commands via UART, and an ESP8266 actuating the motors based on those commands while hosting a safety/override Web Dashboard. The Raspberry Pi will also utilize an IMU (MPU6050) and LEDs/Buzzer for competition-grade state feedback.

Working directory: `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics` and `/Users/roopalisingh/Downloads/TemuFollower`
Integrity mode: benchmark

## Requirements

### R1. Implement Dual-UART Pi Bridge
Refactor the Raspberry Pi's hardware abstraction (`hardware.py`) to send motor commands via Serial. It must attempt to connect via both Hardware UART (`/dev/serial0`) and USB Serial (`/dev/ttyUSB0`) so the user can use either physical connection. Commands must be sent as string formats like `M:<left>,<right>\n`.

### R2. Modify ESP8266 Firmware for UART Parsing
Update the ESP8266 C++ firmware (`main.cpp` and `Motors.cpp`) to constantly listen on `Serial` for the `M:X,Y\n` commands. The firmware must parse the float metrics (-1.0 to 1.0) and accurately map them to the 8-bit PWM scale (-255 to 255) for precise actuation.

### R3. Web Dashboard Safety & Override
Upgrade the ESP8266 HTML/JS Dashboard (`Dashboard.h` and `WebDiagnostics.cpp`) to act as the master safety override. Implement an "Arm/Disarm" toggle (motors must stop instantly if disarmed) and an "Auto / Manual" toggle (enables the Web joystick and ignores UART commands). 

### R4. Integrate Competition Feedback & IMU
Integrate the existing `feedback.py` logic into the Raspberry Pi `main.py` loop. Map the vision detections (Green Dot / Red Dot) and IMU states (stuck detection via `mpu6050`) to the professional audio/visual indicators (LEDs and buzzer).

## Acceptance Criteria

### Serial Bridge Verification
- [ ] A mock Python test or agent inspection confirms `hardware.py` successfully formats commands as `M:X.XX,Y.YY\n` and clamped between -1.0 and +1.0.
- [ ] The `hardware.py` script catches `serial.SerialException` and tries the fallback port gracefully without crashing.

### ESP8266 Firmware Verification
- [ ] Running `pio run` on the `Self_Test_Diagnostics` directory completes successfully with 0 compilation errors.
- [ ] Agent inspection confirms `main.cpp` multiplies incoming serial floats by exactly 255 before passing them to the motor functions.

### Safety Protocol Verification
- [ ] Agent inspection confirms that if the global `g_armed` state is false, `setLeftMotor()` and `setRightMotor()` are explicitly forced to 0 regardless of incoming serial data.

### Feedback Integration Verification
- [ ] Running `python3 -m py_compile main.py` and `python3 -m py_compile feedback.py` completes without syntax errors.
- [ ] The `main.py` loop contains logic to call `FeedbackController`'s LED/buzzer actions when encountering markers or IMU stick states.
