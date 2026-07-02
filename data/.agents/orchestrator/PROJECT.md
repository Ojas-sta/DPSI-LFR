# Project Architecture & Blueprint Specification: DPSI-LFR V2

## Architecture Overview
The DPSI-LFR V2 (Differential Drive Line Following Robot) utilizes an asymmetric dual-brain setup:
1. **ESP32-S3 Microcontroller (Real-Time Control Subsystem)**: Handles low-level motor hardware control, high-frequency sensor sampling, fast PID line following, and IMU heading integration using FreeRTOS multi-core tasks.
2. **Raspberry Pi 4B Single Board Computer (High-Level Vision & Decision Subsystem)**: Handles vision processing via OpenCV on a 20°-tilted camera stream, green-dot intersection navigation, global state machine routing, and web telemetry streaming.

```
+-------------------------------------------------------------+
|                     Raspberry Pi 4B                         |
|  - Python 3 / OpenCV Vision Processing (20° Camera Tilt)     |
|  - Green Dot Intersection & Navigation Logic                |
|  - Master State Machine & Telemetry Web Server              |
+------------------------------+------------------------------+
                               |
                        USB Serial (/dev/ttyUSB0, 115200 baud)
                               |
+------------------------------+------------------------------+
|                        ESP32-S3                             |
|  FreeRTOS Dual-Core Architecture:                            |
|  - Core 0: MPU6050 IMU polling & Z-axis angle integration   |
|  - Core 1: 10x TCRT5000 IR Array, PID Loop, L298N Motors,   |
|            OLED Status UI, Serial Packet Parsing            |
+-------------------------------------------------------------+
```

## Milestones & Work Breakdown
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Technical Blueprints | Create detailed architectural, hardware pinout, FreeRTOS task, vision pipeline, and serial protocol docs in `AI-KOS/knowledge/` and updated `AI-KOS/shared-context/CurrentTask.md`. | None | DONE |
| 2 | M2: Claude Code Master Prompt | Create comprehensive ready-to-use prompt in `AI-KOS/prompts/Claude_Code_Prompt.md`. | M1 | DONE |
| 3 | M3: Review & Verification | Review generated files for consistency, completeness, and adherence to zero-code-generation constraints. | M2 | DONE |

## Output Deliverable Artifacts
- `AI-KOS/knowledge/04 Architecture/Hardware_Pinout_and_Specs.md`
- `AI-KOS/knowledge/04 Architecture/ESP32_FreeRTOS_Architecture.md`
- `AI-KOS/knowledge/04 Architecture/RaspberryPi_Vision_and_Navigation.md`
- `AI-KOS/knowledge/04 Architecture/Serial_Communication_Protocol.md`
- `AI-KOS/knowledge/06 Development/File_Structure_and_Component_Design.md`
- `AI-KOS/shared-context/CurrentTask.md`
- `AI-KOS/prompts/Claude_Code_Prompt.md`
