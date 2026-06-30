# Codebase Analysis & Migration Plan for Two-Node LFR Architecture

This document presents the detailed architectural and codebase analysis for the Line Follower Robot (LFR) migration to a two-node system, consisting of:
1. **Raspberry Pi Node (High-level Perception, Control & Feedback)**
2. **ESP8266 Node (Low-level Motor Actuation & Web Diagnostics)**

---

## 1. Current Codebase Structure & Design Analysis

### A. Raspberry Pi Codebase (`/Users/roopalisingh/Downloads/TemuFollower`)
*   **`main.py`**: The entry point. Coordinates video frame ingestion, runs the Vision Agent's frame processor, invokes the Control Agent to calculate speeds, and writes them to the local GPIO pins via the `RobotHardware` class.
*   **`vision.py`**: Employs a multi-kernel filter bank to isolate the black line (using ROI cropping, Gaussian blurring, adaptive thresholding, and morphological operations), fits a vector heading, and detects red obstacles/red stop lines.
*   **`control.py`**: A state-machine-driven controller (states: `FOLLOWING`, `AVOIDING`, `RECOVERING`, `STOPPED`) using non-linear PID (P error is scaled exponentially to turn sharper for larger deviations) to calculate speeds.
*   **`hardware.py`**: Interfaced with standard RPi GPIO pins (BCM 17 & 27). It historically outputted speed values (0.0 to 1.0) directly as analog voltages using digital outputs.
*   **`feedback.py`**: Integrates LED (Pins 5 and 6) and buzzer (Pin 13) animations to conform to competition rules using `gpiozero` and background threading.

### B. ESP8266 Firmware (`/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`)
*   **`src/main.cpp`**: Bootstraps the NodeMCU AP WiFi, initializes motor PWM pins, starts the AsyncWebServer, and hosts a 20Hz telemetry broadcast loop.
*   **`src/Motors.cpp` & `Motors.h`**: Manages the L298N motor driver using Pins `D1`-`D6` with 8-bit PWM (0-255) at 1kHz. Contains a 500ms safety watchdog (`checkMotorWatchdog`) that halts the motors if no heartbeat is received.
*   **`src/Config.h`**: Keeps SSID definitions and motor pin mapping.
*   **`src/WebDiagnostics.cpp` & `WebDiagnostics.h`**: Implements Async WebSocket handlers, parses WebSocket manual motor joystick inputs, and broadcasts telemetry as JSON.
*   **`src/Dashboard.h`**: Houses the raw HTML/CSS/JS dashboard mockup containing manual motor sliders, a touch-responsive joystick, and a telemetry console.

---

## 2. Concrete Execution Strategy

### Requirement 1: Implement Dual-UART Pi Bridge
*   **File to modify**: RPi's `hardware.py`
*   **Strategy**:
    1.  Remove local GPIO setup for motor pins BCM 17 & 27.
    2.  Import `serial`. Proactively query both `/dev/serial0` (Hardware UART) and `/dev/ttyUSB0` (USB-to-Serial converter) at `115200` baud.
    3.  Cache the successful connection. If both fail, fall back gracefully to simulator/mock mode without raising fatal errors.
    4.  Refactor `set_speeds(left, right)` to:
        *   Clamp left/right float inputs strictly to `[-1.0, 1.0]`.
        *   Encode commands into the format: `M:<left>,<right>\n` (e.g. `M:-0.5000,0.8500\n`).
        *   Write commands to the active serial stream and invoke `flush()`.
        *   Trap `serial.SerialException` inside a `try-except` block to prevent system crashes.

### Requirement 2: Modify ESP8266 Firmware for UART Parsing
*   **Files to modify**: `main.cpp`, `Motors.h`, `Motors.cpp`
*   **Strategy**:
    1.  Introduce a non-blocking `handleSerialInput()` helper function in `main.cpp`'s `loop()`.
    2.  Use a static buffer `rx_buffer[32]` and index to accumulate serial bytes character-by-character.
    3.  Upon detecting `\n` or `\r`, verify if the payload begins with `"M:"`.
    4.  Extract the two float values using `sscanf`.
    5.  Map floats to low-level PWM range by multiplying by exactly `255.0f` (`left_pwm = (int)(left_val * 255.0f)`).
    6.  Constrain the outputs to `[-255, 255]`.
    7.  If the global `g_auto_mode` is `true`, forward the mapped values directly to `setLeftMotor()` and `setRightMotor()`, then call `feedMotorWatchdog()`.

### Requirement 3: Web Dashboard Safety & Override
*   **Files to modify**: `Motors.h`, `Motors.cpp`, `WebDiagnostics.cpp`, `Dashboard.h`
*   **Strategy**:
    1.  Declare global variables `bool g_armed` (default `false` for boot-up safety) and `bool g_auto_mode` (default `true` to prioritize autonomous navigation commands) in `Motors.h`. Expose them to other source modules.
    2.  Enforce Arming constraints in `setLeftMotor(int speed)` and `setRightMotor(int speed)`:
        ```cpp
        if (!g_armed) {
            speed = 0;
        }
        ```
    3.  Upgrade the Web Dashboard HTML (`Dashboard.h`) with two toggle buttons:
        *   `System State: ARMED / DISARMED`
        *   `Control Mode: AUTO / MANUAL`
    4.  When clicked, these buttons emit WebSocket JSON payloads:
        *   `{action: "arm", value: true/false}`
        *   `{action: "mode", value: "auto"/"manual"}`
    5.  In `WebDiagnostics.cpp`, catch these JSON actions:
        *   On `"arm"`, set `g_armed` and if `false`, immediately force both motors to 0.
        *   On `"mode"`, set `g_auto_mode`.
        *   On `"motor"` (manual joystick/sliders), only apply motor changes if `g_auto_mode == false`.
    6.  In `broadcastTelemetry`, append `"armed"` and `"mode"` JSON fields.
    7.  In the dashboard's JavaScript client, read these fields and automatically synchronize the button colors, text, and gray out / disable the joystick/sliders when the system is in `AUTO` mode.

### Requirement 4: Integrate Competition Feedback & IMU
*   **Files to modify**: RPi's `main.py`, `vision.py`, `feedback.py`
*   **Strategy**:
    1.  **Vision Update (`vision.py`)**: Update the HSV filtering in `process_frame()` to look for green-colored circles (Green Dots) by masking `lower_green = [35, 50, 50]` and `upper_green = [85, 255, 255]`. If a green contour with `area > 200` is detected, set `result["green_dot_detected"] = True`.
    2.  **Red Dot Update (`vision.py`)**: Define `result["red_dot_detected"] = True` if the existing red stop line threshold is met.
    3.  **Buzzer Animation (`feedback.py`)**: Update the background blinking thread `_blink_led` to `_blink_led_and_beep(led, buzzer_tone, duration, blink_on, blink_off)`. Use the buzzer to emit distinct sound profiles:
        *   Green Dot: Blink green LED and play C5 (523Hz) tone in sync for 2s (continuing movement).
        *   Red Dot: Blink red LED and play C4 (262Hz) tone in sync for 10s (stopping movement).
        *   Stuck Alarm: Flash red LED rapidly and play A5 (880Hz) tone in sync for 5s.
    4.  **Stuck Detection (`main.py`)**: Create a helper class `StuckDetector` that queries `mpu6050` at address `0x68`. If speeds are commanded (e.g. `>0.1`), but gyro rotation variance remains below a threshold (`<5.0 deg/s`) and accelerometer differential stays static (`<0.1g`) for over `1.5` seconds, declare the robot stuck, halt the motors, and play the rapid stuck alarm.
    5.  **Shutdown Cleanup (`main.py`)**: Ensure `feedback.cleanup()` shuts down both LEDs and stops the buzzer.

---

## 3. Reference to Proposed Source Code Files
The pre-engineered source files have been placed in the explorer directory `/Users/roopalisingh/DPSI-LFR/.agents/explorer_investigate/` as drop-in blueprints:
*   `proposed_hardware.py` (Requirement R1)
*   `proposed_feedback.py` & `proposed_vision.py` & `proposed_main.py` (Requirement R4)
*   `proposed_main.cpp` (Requirement R2)
*   `proposed_Motors.h` & `proposed_Motors.cpp` (Requirement R2 & R3)
*   `proposed_WebDiagnostics.cpp` & `proposed_Dashboard.h` (Requirement R3)
