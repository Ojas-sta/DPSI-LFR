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
