# Original User Request

## 2026-06-29T13:37:35Z

Act as the Lead Architect for the DPSI-LFR V2 Differential Drive Robot. Your task is to generate the comprehensive AI-KOS planning documents (markdown files, architectural diagrams, task breakdowns) that will guide an external AI agent (Claude Code) in writing the actual codebase. **Do NOT write any C++ or Python code.**

Working directory: /Users/roopalisingh/DPSI-LFR

Integrity mode: development

## Requirements

### R1. Technical Blueprint Generation
Generate highly detailed markdown blueprints in `AI-KOS/shared-context/CurrentTask.md` and `AI-KOS/knowledge/` covering the locked-in hardware specs:
- Raspberry Pi 4B (Python OpenCV, 20-degree camera tilt, Green Dot detection).
- ESP32-S3 (C++ FreeRTOS, Core 0 for MPU6050 IMU, Core 1 for PID line following).
- 10x TCRT5000 IR sensors (single wide front array).
- L298N driving 2x 12V 600RPM motors.
- 0.96-inch I2C OLED for debugging (no physical push buttons).
- USB Serial (`/dev/ttyUSB0`) communication between Pi and ESP32.

### R2. External Prompt Creation
Draft an extensive, finalized prompt inside `AI-KOS/prompts/Claude_Code_Prompt.md`. This prompt must synthesize all your architectural decisions and instruct Claude Code exactly how to write the `v2_esp32_firmware` and `v2_pi_core`.

## Acceptance Criteria

### Planning Deliverables
- [ ] Detailed architectural logic and file structures are defined in the `AI-KOS` markdown files.
- [ ] A final, ready-to-copy prompt for Claude Code exists in `AI-KOS/prompts/Claude_Code_Prompt.md`.
- [ ] Absolutely no `.ino`, `.cpp`, or `.py` files are created in the working directory.
