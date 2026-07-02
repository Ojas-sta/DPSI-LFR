# Handoff Report - Line Follower Robot Migration Analysis

## 1. Observation
- **Raspberry Pi Codebase**:
  - `hardware.py`: Interfaced directly with local GPIO (BCM 17 & 27) outputting analog voltages (Lines 52-73). No serial libraries or UART setup.
  - `main.py`: Coordinates flow between `vision.py` and `control.py` and drives `RobotHardware` (Lines 7-62).
  - `vision.py`: Detects black lines and red stop lines/obstacles in HSV (Lines 65-197). Does not contain green color detection logic.
  - `feedback.py`: Defines `FeedbackController` driving Red (Pin 5) and Green (Pin 6) LEDs, and TonalBuzzer (Pin 13) using `gpiozero` (Lines 18-113). Buzzer functions are initialized but never triggered with tone values.
- **ESP8266 Firmware codebase**:
  - `main.cpp`: Starts Access Point `ESP8266-Diagnostics-AP` and initializes motor pins D1-D6 (Lines 12-32). No serial buffer reading/parsing in loop.
  - `Motors.cpp`: Configures 8-bit analog write range for NodeMCU (D1-D6) and handles PWM (Lines 9-60). Incorporates a watchdog timeout of 500ms (Lines 66-75).
  - `WebDiagnostics.cpp` & `Dashboard.h`: Sets up `AsyncWebSocket` server and listens on `/ws` for manual `{action: "motor", left: X, right: Y}` JSON packets, passing them to motor drivers (Lines 11-32).

## 2. Logic Chain
- **Requirement 1 (RPi Dual-UART Pi Bridge)**:
  - Since `hardware.py` currently actuates local GPIO pins (Observation 1), it needs to be modified to import `serial` and sequentially probe `/dev/serial0` and `/dev/ttyUSB0` at 115200 baud to feed the ESP8266. Clamping between -1.0 and 1.0 ensures values map correctly when scaled.
- **Requirement 2 (ESP8266 UART Parsing)**:
  - Since `main.cpp` currently has no serial-reading loop (Observation 2), a non-blocking UART reader accumulating character payloads into a static buffer is necessary. Floats scaled by exactly 255 map to NodeMCU's 8-bit `analogWrite` range (Observation 2).
- **Requirement 3 (Safety Dashboard Toggles)**:
  - Currently, any client connecting to the web dashboard can command speeds using websocket `motor` actions (Observation 2). Introducing a global `g_armed` (forces 0 outputs inside `setLeftMotor` and `setRightMotor` in `Motors.cpp`) and a `g_auto_mode` state (gates serial commands and websocket commands) provides a master safety system. Synced UI buttons prevent conflicting inputs.
- **Requirement 4 (Perception Feedback & Stuck Alarm)**:
  - `vision.py` lacks green detection, and `feedback.py` does not play buzzer tones (Observation 1). Adding green HSV masks to `vision.py` and upgrading `_blink_led` in `feedback.py` to synchronize tone generation enables compliant audio/visual signals. Integrating `mpu6050` readings into `main.py` creates a feedback loop to halt the system and trigger rapid flashing/beeping if the robot is physically stationary while speeds are commanded.

## 3. Caveats
- No physical MPU6050 hardware or serial communication line was attached during this read-only review, so mock-based verification is used.
- The I2C address of the MPU6050 is assumed to be `0x68` (industry standard).
- PiCamera dependency might require legacy camera interface enablement on Raspberry Pi Bullseye/Bookworm OS.

## 4. Conclusion
The codebase is fully analyzed and the required migration strategy is mapped out. Specific proposed files have been created in the agent's folder `/Users/roopalisingh/DPSI-LFR/.agents/explorer_investigate/` which act as drop-in blueprints for the next phase.

## 5. Verification Method
- **Files to Inspect**:
  - Check the proposed files in `.agents/explorer_investigate/` directory:
    - `proposed_hardware.py`
    - `proposed_main.py`
    - `proposed_feedback.py`
    - `proposed_vision.py`
    - `proposed_main.cpp`
    - `proposed_Motors.h`
    - `proposed_Motors.cpp`
    - `proposed_WebDiagnostics.cpp`
    - `proposed_Dashboard.h`
- **Build / Test Verification**:
  - The ESP8266 project compiles successfully under PlatformIO using the command:
    ```bash
    pio run
    ```
    run from `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`.
  - The Raspberry Pi code can be verified by launching:
    ```bash
    python main.py
    ```
    run from `/Users/roopalisingh/Downloads/TemuFollower` using Python 3, verifying it handles camera/serial initialization gracefully even when simulated.
