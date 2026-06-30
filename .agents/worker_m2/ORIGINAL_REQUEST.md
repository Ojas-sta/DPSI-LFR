## 2026-06-29T14:23:46Z

Role: Specialist Worker for Claude Code Master Prompt Creation
Working Directory: /Users/roopalisingh/DPSI-LFR/.agents/worker_m2

Task Objective:
Draft an extensive, finalized, ready-to-copy master prompt inside `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/prompts/Claude_Diagnostics_Prompt.md`.

Context & Technical Hardware References (from `v2_esp32_firmware/Config.h`):
- Microcontroller: ESP32-S3.
- Goal of Prompt: Instruct Claude Code (an autonomous AI coding assistant) to generate complete, production-grade diagnostic firmware for ESP32-S3 that temporarily replaces the main FreeRTOS line-following code for physical hardware testing.
- Features required in firmware to be built by Claude Code:
  1. Wi-Fi Access Point (SSID: `ESP32-Diagnostics-AP`, IP: `192.168.4.1`).
  2. Async Web Server serving an embedded single-page HTML/CSS/JS dashboard.
  3. WebSocket server handling low-latency motor control commands and real-time telemetry streaming.
  4. L298N Motor control using ESP32-S3 LEDC PWM (Left: ENA 11, IN1 12, IN2 13; Right: ENB 47, IN3 14, IN4 21; 20kHz, 8-bit). Include 500ms safety watchdog auto-stop.
  5. 10x IR Sensor Array reading on GPIOs 1, 2, 4, 5, 6, 7, 15, 16, 17, 18, streaming bitmask at 20Hz.

Prompt Design Requirements for `Claude_Diagnostics_Prompt.md`:
- Must be structured clearly with markdown headers, code blocks, pin tables, and operational requirements.
- Must provide exact step-by-step instructions for Claude Code on project structure (e.g., PlatformIO / Arduino IDE setup), library dependencies (`ESPAsyncWebServer`, `AsyncTCP`, `ArduinoJson`), C++ implementation details, embedded HTML/JS string literal creation, and verification steps.
- Must explicitly instruct Claude Code on coding standards, zero-delay execution, safety watchdogs, and clear logging via Serial.

STRICT CONSTRAINT:
Do NOT create any `.ino`, `.cpp`, `.h`, or `.py` code files. ONLY create `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/prompts/Claude_Diagnostics_Prompt.md`.

## 2026-06-30T14:46:39Z

/goal

Apply the proposed Python Curses TUI and Serial changes for Milestone 2:
1. Replace `rbpi_package/cli.py` with the contents of `/Users/roopalisingh/DPSI-LFR/.agents/explorer_m2/proposed_cli.py`.
2. Replace `rbpi_package/hardware.py` with the contents of `/Users/roopalisingh/DPSI-LFR/.agents/explorer_m2/proposed_hardware.py`.
Wait, do not write code directly using file creation tools unless they are the designated tools for file modification. Use your tools to make the code changes.
3. Verify the changes by running unit tests from within `rbpi_package` directory:
   `python3 -m unittest test_hardware.py`
4. Verify syntax correctness of `cli.py` and `hardware.py`:
   `python3 -m py_compile rbpi_package/cli.py rbpi_package/hardware.py`
5. Write a handoff report in `/Users/roopalisingh/DPSI-LFR/.agents/worker_m2/handoff.md` summarizing the changes, commands run, and test outputs.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

