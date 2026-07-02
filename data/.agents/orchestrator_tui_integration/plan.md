# Execution Plan: TUI and Firmware Integration

## Milestones and Objectives
1. **Milestone 1: ESP8266 Ping-Pong Firmware (`Self_Test_Diagnostics/src/main.cpp`)**
   - Goal: Add parsing for `P\n` command so it replies with `P_ACK\n` over Serial.
   - Verification: Compile successfully with `pio run`.

2. **Milestone 2: TUI Overhaul & UART Connectivity (`rbpi_package/cli.py` & `rbpi_package/hardware.py`)**
   - Goal: Implement the new curses dashboard with theme, ascii-art, 3-wheel differential chassis, speed caps (`[` / `]` keys), LED/Buzzer toggle commands, default `/dev/serial0` (toggleable to `/dev/ttyUSB0`), serial monitor panel, and the ping-pong thread.
   - Verification: Compile successfully with `python3 -m py_compile rbpi_package/cli.py`.

3. **Milestone 3: Verification & Integration Testing**
   - Goal: Run static check, compile diagnostics, check UI behavior, run a Forensic Auditor.
   - Verification: Passing all tests, review reports, and Forensic Auditor CLEAN verdict.
