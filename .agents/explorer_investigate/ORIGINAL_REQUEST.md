## 2026-06-30T12:01:32Z
Analyze the codebase and migrate requirements for the Line Follower robot two-node architecture.

Working directories:
- Raspberry Pi code: `/Users/roopalisingh/Downloads/TemuFollower`
- ESP8266 Firmware: `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`

Original Request Requirements:
- R1. Implement Dual-UART Pi Bridge: Refactor RPi's `hardware.py` to send motor commands via Serial. Attempt to connect via both Hardware UART (`/dev/serial0`) and USB Serial (`/dev/ttyUSB0`). Send commands as string formats like `M:<left>,<right>\n`, clamping values between -1.0 and +1.0. Catch `serial.SerialException` and fallback gracefully.
- R2. Modify ESP8266 Firmware for UART Parsing: Update `main.cpp` and `Motors.cpp` to listen on `Serial` for `M:X,Y\n` commands. Multiply incoming serial floats by exactly 255 before passing them to motor functions (mapping -1.0..1.0 to -255..255).
- R3. Web Dashboard Safety & Override: Upgrade `Dashboard.h` and `WebDiagnostics.cpp` to act as master safety override. Implement "Arm/Disarm" toggle (if global `g_armed` is false, force `setLeftMotor()` and `setRightMotor()` to 0) and "Auto / Manual" toggle (enables Web joystick and ignores UART commands).
- R4. Integrate Competition Feedback & IMU: Integrate existing `feedback.py` logic into RPi `main.py` loop. Map vision detections (Green Dot / Red Dot) and IMU states (stuck detection via `mpu6050` sensor) to audio/visual indicators (LEDs and buzzer).

Tasks for you:
1. Examine all existing files in both directories (in particular: `hardware.py`, `main.py`, `feedback.py`, `main.cpp`, `Motors.cpp`, `Motors.h`, `Dashboard.h`, `WebDiagnostics.cpp`, `WebDiagnostics.h`).
2. Document the current code structure, functions, variables, and design.
3. Formulate a detailed, concrete execution strategy for how to implement requirements R1, R2, R3, and R4.
4. Save your findings to `/Users/roopalisingh/DPSI-LFR/.agents/explorer_investigate/analysis.md`.
5. Report back when done.
