# Migration Plan: Line Follower Robot Two-Node Architecture

This document describes the plan for migrating the Line Follower Robot to a two-node system.

## Milestones and Objectives

### Milestone 1: Implement Dual-UART Pi Bridge (Requirement R1)
- **Goal**: Refactor `hardware.py` on the Raspberry Pi side.
- **Tasks**:
  - Load `proposed_hardware.py` prepared by the explorer.
  - Implement serial connection with fallback (primary `/dev/serial0`, secondary `/dev/ttyUSB0`, 115200 baud).
  - Implement `set_speeds(left, right)` to clamp inputs to `[-1.0, 1.0]` and send commands as `M:L,R\n`.
  - Gracefully handle `serial.SerialException` by falling back to simulation if no hardware is present.
- **Verification**: Run `python3 -m py_compile hardware.py` and run a mock test script.

### Milestone 2: ESP8266 UART Parsing & Motor Scaling (Requirement R2)
- **Goal**: Implement non-blocking serial reading and command execution on ESP8266.
- **Tasks**:
  - Load `proposed_main.cpp`, `proposed_Motors.h`, and `proposed_Motors.cpp`.
  - Add character-accumulating serial reading to `main.cpp`.
  - Multiply incoming serial floats by exactly 255.0f to scale to 8-bit PWM (`[-255, 255]`).
  - Constrain scaled values and apply to motors when in `auto` mode.
- **Verification**: Ensure the firmware compiles with `pio run` in `Self_Test_Diagnostics`.

### Milestone 3: Web Dashboard Safety & Override (Requirement R3)
- **Goal**: Add Arm/Disarm and Auto/Manual safety toggles to the Web Dashboard.
- **Tasks**:
  - Add global `g_armed` (forces 0 output in `setLeftMotor` and `setRightMotor`) and `g_auto_mode` variables.
  - Update `Dashboard.h` with System State and Control Mode toggles.
  - Update `WebDiagnostics.cpp` to parse `arm` and `mode` WebSocket commands, and serialize telemetry.
- **Verification**: Ensure successful PlatformIO compilation. Verify logical correctness in motor functions.

### Milestone 4: Competition Feedback & IMU Integration (Requirement R4)
- **Goal**: Integrate green marker detection, buzzer animations, and MPU6050 stuck detection.
- **Tasks**:
  - Load `proposed_vision.py`, `proposed_feedback.py`, and `proposed_main.py`.
  - Add green color contour detection in `vision.py`.
  - Update `feedback.py` to synchronize LED blinking and tonal buzzer (green dot: green LED + C5 tone for 2s; red dot: red LED + C4 tone for 10s; stuck: red LED + A5 tone for 5s).
  - Add MPU6050 stuck detection inside `main.py`.
- **Verification**: Check syntax of Python scripts with `py_compile`. Verify main loop integrations.

### Milestone 5: E2E System Verification
- **Goal**: Verify that all components compile, execute syntactically, and work together.
- **Tasks**:
  - Compile the entire ESP8266 project (`pio run`).
  - Run syntactical validation on RPi python scripts.
  - Audit the final code for integrity and completeness.
