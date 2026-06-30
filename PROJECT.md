# Project: DPSI-LFR TUI & ESP8266 Overhaul

## Architecture
- **Two-node Architecture**: Raspberry Pi 4B (vision/metrics/TUI CLI) and ESP8266 (motor actuation and web diagnostics).
- **Communication Link**: Serial over UART (`/dev/serial0` or `/dev/ttyUSB0`) at 115,200 baud.
- **Message Protocols**:
  - Motor Commands: `M:<left_speed>,<right_speed>\n`
  - Arm Command: `A:<0 or 1>\n`
  - Mode Command: `C:<0 or 1>\n`
  - Ping Command: `P\n`
  - Pong Command: `P_ACK\n`
- **TUI Component (`cli.py`)**:
  - Curses-based interface with blue (`curses.COLOR_BLUE`) and purple/magenta (`curses.COLOR_MAGENTA`) styling.
  - Centered ASCII art display at the top from `ascii-art.txt`.
  - Connection status badge showing `[ CONNECTED ]` (green) or `[ DISCONNECTED ]` (red) based on 1s ping-pong protocol.
  - 3-wheel differential chassis telemetry (rear left, rear right, front caster) with color-coded wheel speeds (green for positive, red for negative).
  - IMU heading (Z-axis gyro integration) and speed limit adjustments using keys `[` and `]`.
  - Bordered sub-window for the live Serial monitor panel showing the last 10 lines of incoming data.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | ESP8266 Ping-Pong Command | Add `P\n` parsing and `P_ACK\n` response to ESP8266 firmware | None | DONE (c064b9d0-954e-4ef2-be28-57798a6c2fbf) |
| M2 | Curses TUI Layout & Theme | Implement blue/magenta curses layout, render ascii-art.txt centered | None | DONE (0434a275-cb55-47fe-b85f-cc0f90988208) |
| M3 | UART Connection Status | Background thread for 1s ping sending, 500ms timeout check, status badge | M1 | DONE (0434a275-cb55-47fe-b85f-cc0f90988208) |
| M4 | Robot Telemetry & Speed Colors | Draw 3-wheel chassis, color-coded speeds next to rear wheels | M2 | DONE (0434a275-cb55-47fe-b85f-cc0f90988208) |
| M5 | IMU Heading & Speed Limits | MPU6050 Z-axis gyro integration, speed limits [ / ] keys, L / B indicators | M2 | DONE (0434a275-cb55-47fe-b85f-cc0f90988208) |
| M6 | Live Serial Monitor Panel | Bordered sub-window displaying rolling 10 lines of incoming serial data | M2, M3 | DONE (0434a275-cb55-47fe-b85f-cc0f90988208) |
| M7 | E2E Integration Verification | Final verification of all combined requirements (TUI controls, ESP8266 response, compile & run tests) | M1 to M6 | DONE (00a22717-337e-4f02-863e-c1ea9d43cbf0) |

## Code Layout
- `/Users/roopalisingh/DPSI-LFR/rbpi_package/cli.py` - TUI dashboard interface
- `/Users/roopalisingh/DPSI-LFR/rbpi_package/hardware.py` - Hardware interface for serial
- `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/src/main.cpp` - ESP8266 main loop and UART command parser
- `/Users/roopalisingh/DPSI-LFR/ascii-art.txt` - ASCII Art text file

## Interface Contracts
### Raspberry Pi ↔ ESP8266 (Serial Text Protocol)
- `M:<left>,<right>\n`: Float values in range [-1.0, 1.0].
- `A:<val>\n`: integer 0 or 1.
- `C:<val>\n`: integer 0 or 1.
- `P\n`: Connection ping, no arguments.
- `P_ACK\n`: Connection acknowledgement, sent by ESP8266 immediately on receipt of `P\n`.
