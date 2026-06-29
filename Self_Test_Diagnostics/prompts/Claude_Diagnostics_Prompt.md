# ESP32-S3 Hardware Diagnostics Firmware Master Prompt for Claude Code

> **Instruction to User:** Copy and paste the entire block below into Claude Code (or any autonomous AI coding assistant) within your project repository directory.

---

```markdown
# TASK SPECIFICATION: ESP32-S3 Hardware Diagnostics Web GUI & Control Firmware

## 1. System Role & Context
You are acting as an expert Embedded Systems Firmware Engineer specializing in ESP32-S3 microcontrollers, Real-Time Operating Systems (FreeRTOS), asynchronous network communications, and web-based hardware diagnostics.

Your objective is to generate complete, production-grade diagnostic firmware for the **DPSI-LFR (Dual-Phase Smart Inspection Line-Following Robot)** powered by an **ESP32-S3**. This diagnostic firmware serves as a temporary operational replacement for the main line-following algorithms. It enables engineers to conduct physical hardware testing, sensor calibration, and motor driver verification via an airborne Wi-Fi Access Point and responsive WebSocket web dashboard.

---

## 2. Hardware Mapping & Pin Definitions Reference Table

You must strictly adhere to the physical GPIO assignments and hardware parameters defined in the system's core configuration (`v2_esp32_firmware/Config.h`):

### 2.1 L298N Motor Driver Pins & PWM Configuration
| Subsystem | Signal Name | ESP32-S3 GPIO Pin | Configuration / PWM Parameters |
|---|---|---|---|
| **Left Motor** | ENA (PWM) | `GPIO 11` | LEDC Channel 0, 20kHz Frequency, 8-bit Resolution (0–255) |
| | IN1 (Dir A) | `GPIO 12` | Digital Output (Standard GPIO) |
| | IN2 (Dir B) | `GPIO 13` | Digital Output (Standard GPIO) |
| **Right Motor**| ENB (PWM) | `GPIO 47` | LEDC Channel 1, 20kHz Frequency, 8-bit Resolution (0–255) |
| | IN3 (Dir A) | `GPIO 14` | Digital Output (Standard GPIO) |
| | IN4 (Dir B) | `GPIO 21` | Digital Output (Standard GPIO) |

### 2.2 10x TCRT5000 IR Sensor Array GPIO Mapping
| Sensor Index | Physical Position | ESP32-S3 GPIO Pin | Input Mode | Bitmask Shift |
|---|---|---|---|---|
| IR 1 | Far Left | `GPIO 1` | `INPUT` / Digital Read | `Bit 0` (0x001) |
| IR 2 | Left 2 | `GPIO 2` | `INPUT` / Digital Read | `Bit 1` (0x002) |
| IR 3 | Left 3 | `GPIO 4` | `INPUT` / Digital Read | `Bit 2` (0x004) |
| IR 4 | Left 4 | `GPIO 5` | `INPUT` / Digital Read | `Bit 3` (0x008) |
| IR 5 | Center Left | `GPIO 6` | `INPUT` / Digital Read | `Bit 4` (0x010) |
| IR 6 | Center Right | `GPIO 7` | `INPUT` / Digital Read | `Bit 5` (0x020) |
| IR 7 | Right 4 | `GPIO 15` | `INPUT` / Digital Read | `Bit 6` (0x040) |
| IR 8 | Right 3 | `GPIO 16` | `INPUT` / Digital Read | `Bit 7` (0x080) |
| IR 9 | Right 2 | `GPIO 17` | `INPUT` / Digital Read | `Bit 8` (0x100) |
| IR 10 | Far Right | `GPIO 18` | `INPUT` / Digital Read | `Bit 9` (0x200) |

### 2.3 Additional Hardware & Timing Parameters
- **Serial Console**: Baud Rate `115200` baud on USB Serial.
- **Motor Safety Watchdog Timeout**: `500 ms` (Automatic emergency motor shutdown if no control packet is received).
- **Telemetry Update Rate**: `20 Hz` (Every `50 ms`).

---

## 3. Required Firmware Subsystems & Functional Specifications

You must generate firmware implementing the following five core subsystems:

### Subsystem 1: Wi-Fi Access Point (SoftAP)
- **SSID**: `ESP32-Diagnostics-AP`
- **Password**: None (Open network) or `diagnostics123` (Configurable macro).
- **Static IP Configuration**:
  - IP Address: `192.168.4.1`
  - Gateway: `192.168.4.1`
  - Subnet Mask: `255.255.255.0`
- **Behavior**: On boot, initialize SoftAP mode, log the AP status and local IP to the Serial console, and begin listening for incoming client connections.

### Subsystem 2: Async Web Server & Embedded Dashboard
- Utilize `ESPAsyncWebServer` to serve a single-page web dashboard on standard HTTP port `80`.
- The HTML, CSS, and JavaScript must be compressed and embedded directly within the C++ firmware header/source using `PROGMEM` string literals (`const char INDEX_HTML[] PROGMEM = R"rawliteral(...)rawliteral";`).
- The root path `/` must serve this embedded document with MIME type `text/html`.

### Subsystem 3: Full-Duplex WebSocket Server (`/ws`)
- Attach an `AsyncWebSocket` instance to `/ws`.
- **Incoming Motor Commands**: Parse incoming JSON packets formatted as:
  ```json
  {"action": "motor", "left": 180, "right": -180}
  ```
  *(Positive values indicate forward direction, negative values indicate reverse direction, 0 indicates stop. Valid range: -255 to 255)*.
- **Outgoing Real-Time Telemetry Streaming**: Stream system status at 20Hz (50ms intervals) to all connected WebSocket clients formatted as:
  ```json
  {
    "type": "telemetry",
    "uptime_ms": 124500,
    "ir_raw": 896,
    "ir_bits": [0,0,0,0,0,0,1,1,1,0],
    "motors": {"left": 180, "right": -180},
    "watchdog_ok": true
  }
  ```
- Manage client connection/disconnection events cleanly, logging event details to Serial.

### Subsystem 4: L298N Motor Control & 500ms Watchdog Security
- Implement motor direction logic using truth tables for `IN1`/`IN2` (Left Motor) and `IN3`/`IN4` (Right Motor):
  - Forward: `IN1=HIGH, IN2=LOW` (Speed = PWM)
  - Reverse: `IN1=LOW, IN2=HIGH` (Speed = PWM)
  - Stop/Brake: `IN1=LOW, IN2=LOW` (Speed = 0)
- **LEDC PWM Hardware Handling**:
  - Attach PWM pins (`ENA` pin 11, `ENB` pin 47) to LEDC channels 0 and 1 at 20kHz with 8-bit resolution.
  - Write helper functions `setLeftMotor(int speed)` and `setRightMotor(int speed)`.
- **Safety Watchdog Auto-Stop**:
  - Track `last_motor_command_time` via `millis()`.
  - In the main loop (or dedicated background task), check if `(millis() - last_motor_command_time > 500)`.
  - If timeout occurs while motors are running, force immediate emergency stop (`setLeftMotor(0)`, `setRightMotor(0)`), log a warning to Serial, and set `watchdog_ok` status to `false` in telemetry.

### Subsystem 5: Non-Blocking 10x IR Sensor Array Reader
- Configure GPIOs 1, 2, 4, 5, 6, 7, 15, 16, 17, and 18 as digital inputs.
- Read all 10 GPIO pins during each 20Hz telemetry cycle using non-blocking timing (`millis()`).
- Assemble digital state bits into a 16-bit integer bitmask (`ir_raw`) and an array of individual boolean/integer bits (`ir_bits`) for easy parsing by the web GUI.

---

## 4. Single-Page Embedded Web Dashboard Requirements (HTML/CSS/JS)

The embedded HTML/CSS/JS web dashboard must be modern, responsive, visually clean, and self-contained (no external CDN dependencies). It must include:

1. **Header & Status Banner**:
   - Title: "ESP32-S3 Hardware Diagnostics Dashboard".
   - Live WebSocket connection status indicator badge (Green = "Connected", Red = "Disconnected / Reconnecting").
   - System Uptime counter.
2. **Motor Control Panel**:
   - **Interactive Touch / Mouse D-Pad**: Directional buttons for Forward, Reverse, Spin Left, Spin Right, and Emergency Stop.
   - **Dual Speed Sliders**: Independent range sliders for Left Motor Speed (-255 to 255) and Right Motor Speed (-255 to 255) with real-time numerical feedback.
   - **Keyboard Driving Controls**: Support for WASD or Arrow keys for physical keyboard driving during testing.
3. **10x IR Sensor Visualization Bar**:
   - A horizontal visual representation of the 10 IR sensors (labelled IR1 through IR10).
   - Dynamic LED indicator boxes that light up bright green/cyan when line reflection is detected (logical 1) and dark gray when clear (logical 0).
   - Numerical display of raw bitmask integer and hex values.
4. **Live Telemetry & Diagnostics Console**:
   - Terminal-style text log output window showing recent events, WebSocket messages, and watchdog state alerts.

---

## 5. Project Structure & Build Configuration

You must organize the generated code into a production-ready repository structure supporting either PlatformIO or Arduino IDE.

### 5.1 PlatformIO Configuration (`platformio.ini`)
Provide a complete `platformio.ini` file configured as follows:
```ini
[env:esp32s3_diagnostics]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200
build_flags = 
    -D CORE_DEBUG_LEVEL=3
    -D CONFIG_ARDUINO_LOOP_STACK_SIZE=8192
lib_deps =
    https://github.com/me-no-dev/ESPAsyncWebServer.git
    https://github.com/me-no-dev/AsyncTCP.git
    bblanchon/ArduinoJson @ ^6.21.3
```

### 5.2 Source Code File Layout
Organize the code modularly across cleanly separated files inside `Self_Test_Diagnostics/src/` (or single file for simple compilation if requested):
- `main.cpp` (or `Self_Test_Diagnostics.ino`): Core setup, loop, non-blocking timing, and subsystem orchestration.
- `Config.h`: Hardware pin mappings, PWM frequencies, Wi-Fi credentials, and timing constants.
- `Motors.h` / `Motors.cpp`: LEDC PWM setup, directional pin outputs, motor speed setters, and watchdog logic.
- `Sensors.h` / `Sensors.cpp`: IR array pin initialization and bitmask reading functions.
- `WebDiagnostics.h` / `WebDiagnostics.cpp`: AsyncWebServer setup, WebSocket event handling, JSON parsing/formatting, and embedded HTML header definitions.
- `Dashboard.h`: Embedded `PROGMEM` HTML/CSS/JS raw literal string.

---

## 6. Strict Implementation Guidelines & Coding Standards

1. **Zero-Delay Execution Rule**: You MUST NOT use `delay()` or `vTaskDelay()` anywhere in the main loop or network callbacks. All periodic tasks (telemetry streaming, watchdog checks, sensor polling) must use non-blocking timestamps (`millis()`).
2. **ESP32 Arduino Core Compatibility**: Ensure compatibility with both ESP32 Arduino Core v2.x and v3.x. Use modern LEDC functions (`ledcAttachChannel` or conditional macros for `ledcSetup`/`ledcAttachPin`).
3. **Robust Memory Management**: Use standard static allocations or small `ArduinoJson` dynamic buffers (`StaticJsonDocument<512>`) to prevent memory fragmentation or stack overflow in WebSocket callbacks.
4. **Comprehensive Serial Logging**: Include clear, structured Serial logging statements using `Serial.printf()` formatted with timestamps and subsystem tags (e.g., `[SYS]`, `[WIFI]`, `[WS]`, `[MOTOR]`, `[WATCHDOG]`).

---

## 7. Verification & Operational Test Procedure

After generating the code, provide a detailed operational verification guide outlining how to test the compiled firmware:

1. **Serial Console Verification**: Open Serial Monitor at 115200 baud. Confirm AP startup message and verify local IP is `192.168.4.1`.
2. **Network Connection Test**: Connect host PC or mobile device to Wi-Fi SSID `ESP32-Diagnostics-AP`. Verify IP assignment via ping to `192.168.4.1`.
3. **Web Dashboard Load**: Open web browser and navigate to `http://192.168.4.1`. Verify dashboard renders and WebSocket status turns green ("Connected").
4. **Motor Direction & Safety Watchdog Verification**:
   - Command forward motor movement via dashboard sliders or D-Pad. Observe wheel rotation.
   - Disconnect Wi-Fi or stop sending WebSocket packets. Verify motors immediately shut down within 500ms and Serial logs a watchdog alert.
5. **IR Sensor Verification**:
   - Pass an object or line under each TCRT5000 IR sensor individually (IR 1 through IR 10).
   - Confirm that the corresponding indicator LED on the web dashboard updates in real-time at 20Hz.

---

### EXECUTION INSTRUCTION FOR CLAUDE CODE:
Now, generate all necessary source code files, header files, configuration files, and HTML templates according to the specifications above. Write the completed files directly into the repository project tree under `Self_Test_Diagnostics/`.
```
