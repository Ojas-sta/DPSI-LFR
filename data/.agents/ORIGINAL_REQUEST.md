# Original User Request

## Initial Request — 2026-06-29T08:52:48Z

<USER_REQUEST>
Generate the architectural blueprints and the final Claude Code prompt for a **Diagnostics & Telemetry Build** for the ESP32-S3. This build is intended for rapid hardware validation, providing a high-speed Wi-Fi Access Point (AP) web server that streams real-time IR sensor data and accepts low-latency manual motor commands (forward, back, left, right).

Working directory: /Users/roopalisingh/DPSI-LFR

Integrity mode: development

## Requirements

### R1. Technical Blueprint Generation
Generate detailed markdown blueprints in `Self_Test_Diagnostics/knowledge/` covering:
- **Web Server Architecture**: An ESP32-S3 AP hosting an asynchronous, high-speed web server (e.g., using WebSockets or Server-Sent Events) to minimize latency.
- **Motor Control**: Basic directional mappings (forward, reverse, left, right) utilizing the existing `Config.h` and L298N pinouts.
- **Telemetry**: Real-time reading of the 10x IR array and broadcasting the raw bitmask/values to the web client.
- **Constraint**: This is a standalone diagnostic firmware. It temporarily replaces the main V2 FreeRTOS firmware to allow the user to immediately test physical motor and sensor wiring.

### R2. External Prompt Creation
Draft an extensive, finalized prompt inside `Self_Test_Diagnostics/prompts/Claude_Diagnostics_Prompt.md`. This prompt must instruct Claude Code exactly how to write this diagnostic Web Server firmware using the ESP32-S3.

## Acceptance Criteria

### Planning Deliverables
- [ ] Detailed web server architecture, UI layout for the testing dashboard, and motor logic are defined in the `Self_Test_Diagnostics/knowledge/` markdown files.
- [ ] A final, ready-to-copy prompt for Claude Code exists in `Self_Test_Diagnostics/prompts/Claude_Diagnostics_Prompt.md`.
- [ ] Absolutely no `.ino`, `.cpp`, `.h`, or `.py` files are created by the teamwork agents.
</USER_REQUEST>

## Follow-up — 2026-06-30T20:01:11+05:30

<USER_REQUEST>
/goal

Overhaul the Raspberry Pi Curses TUI dashboard to add detailed ASCII robot telemetry, real-time ESP8266 serial connection status via a new ping-pong protocol, local IMU angle integration, and manual speed limits. Also update the ESP8266 diagnostics firmware to support the ping command.

Working directory: `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics` and `/Users/roopalisingh/DPSI-LFR/rbpi_package`
Integrity mode: benchmark

## Requirements

### R1. ESP8266 Ping-Pong Command
Update the ESP8266 C++ firmware (`main.cpp`) to parse the command `P\n` over Serial and immediately print `P_ACK\n` back.

### R2. Curses TUI Redesign (Antigravity Blue-Purple Theme)
Overhaul the Raspberry Pi CLI (`cli.py`) with a professional curses interface using blue (`curses.COLOR_BLUE`) and purple/magenta (`curses.COLOR_MAGENTA`) styling. Read and render `ascii-art.txt` centered at the top.

### R3. UART Ping-Pong Connection Status
Implement a background thread in `cli.py` that sends `P\n` to the ESP8266 every 1 second and checks for `P_ACK\n` within 500ms. Show a green `[ CONNECTED ]` or red `[ DISCONNECTED ]` status badge in the TUI based on response.

### R4. Detailed 3-Wheel Robot Telemetry & Color Speeds
Draw a detailed 3-wheel differential ASCII chassis (2 rear wheels + 1 front caster). Display the left and right wheel speeds directly next to the rear wheels, color-coded in green (positive speeds, e.g. `+80% ▲`) and red (negative speeds, e.g. `-50% ▼`).

### R5. IMU Heading & Speed Limits
- Add a thread in `cli.py` reading the MPU6050 Z-axis gyro to calculate and show the real-time heading angle and an ASCII arrow pointing in that direction (e.g. `[ ↗ ] 45°`).
- Implement speed caps adjusted using the `[` and `]` keys (10% steps, from 10% to 100%).

### R6. Live Serial Monitor Panel
Create a bordered sub-window at the bottom of the TUI showing a rolling history of the last 10 lines of incoming Serial telemetry from the ESP8266.

## Acceptance Criteria

### ESP8266 Code
- [ ] Running `pio run` in the `Self_Test_Diagnostics` directory finishes with 0 compilation errors.
- [ ] Code parsing `P` and responding `P_ACK` is implemented and verified.

### CLI Package
- [ ] Running `python3 -m py_compile cli.py` finishes without syntax errors.
- [ ] Verification script or agent inspection confirms the TUI has the `[` and `]` key binds, `L` and `B` indicators, and color-coded wheel speed rendering.
</USER_REQUEST>

## Follow-up — 2026-06-30T20:08:11+05:30

<USER_REQUEST>
/goal

# Teamwork Project Prompt — TUI and Firmware Integration

Implement a fully featured Python Curses TUI (`lfr-cli`) for the Raspberry Pi that features detailed ASCII art, live colored motor speed indicators, and a UART ping-pong protocol, alongside the corresponding C++ firmware updates for the ESP Motor Node.

Working directory: /Users/roopalisingh/DPSI-LFR
Integrity mode: development

## Requirements

### R1. TUI Overhaul (`rbpi_package/cli.py`)
Implement a blue/purple themed `curses` interface. It must read and render the contents of `ascii-art.txt` at the top. It must include a detailed 3-wheel ASCII robot visualization showing real-time motor speeds directly next to the wheels in green (forward) and red (reverse). It must feature keyboard controls for setting speed caps, toggling LEDs/Buzzer, and switching serial ports.

### R2. UART Connectivity & Monitor (`rbpi_package/hardware.py` & `cli.py`)
Implement a background thread to read non-blocking serial lines from the ESP motor node and display them in a live scrolling "Serial Monitor" box inside the TUI. The serial connection should **default to UART (`/dev/serial0`)** but allow the user to easily toggle to USB Serial (`/dev/ttyUSB0`) from the UI. The Python code must also continually send `P\n` to ping the ESP and use the replies to update a live "CONNECTED/DISCONNECTED" status badge.

### R3. Motor Node Firmware Update (`Self_Test_Diagnostics/src/main.cpp`)
Update the ESP C++ firmware to support the ping protocol. Add parsing for the `P\n` command so it immediately replies with `P_ACK\n` over Serial.

## Acceptance Criteria

### Compilation & Syntax
- [ ] Running `python3 -m py_compile rbpi_package/cli.py` completes with 0 errors.
- [ ] Running `pio run` in `Self_Test_Diagnostics` completes with 0 errors.

### TUI Verification
- [ ] An agent inspection verifies that `cli.py` successfully reads and prints the `ascii-art.txt` file.
- [ ] An agent inspection verifies that `cli.py` uses `curses.COLOR_GREEN` and `curses.COLOR_RED` to color the motor speed text based on positive or negative values.
- [ ] An agent inspection verifies that `cli.py` allows toggling between `/dev/serial0` and `/dev/ttyUSB0`.
</USER_REQUEST>
