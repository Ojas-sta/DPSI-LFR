# Project Architecture & Blueprint Specification: DPSI-LFR V2

## Architecture Overview
The DPSI-LFR V2 (Differential Drive Line Following Robot) utilizes a asymmetric dual-brain setup:
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
| 1 | M1: Technical Blueprints | Create detailed architectural, hardware pinout, FreeRTOS task, vision pipeline, and serial protocol docs in `AI-KOS/knowledge/` and updated `AI-KOS/shared-context/CurrentTask.md`. | None | IN_PROGRESS |
| 2 | M2: Claude Code Master Prompt | Create comprehensive ready-to-use prompt in `AI-KOS/prompts/Claude_Code_Prompt.md`. | M1 | PLANNED |
| 3 | M3: Review & Verification | Review generated files for consistency, completeness, and adherence to zero-code-generation constraints. | M2 | PLANNED |

## Detailed File Layouts to be Designed
### ESP32 Firmware Target (`v2_esp32_firmware/`)
- `v2_esp32_firmware.ino`: Setup, main loop (Core 1) running PID & Serial.
- `Config.h`: Complete GPIO mapping for L298N, IR array, I2C bus, PWM channels.
- `IMU_Task.h`: Core 0 FreeRTOS task for MPU6050 polling and gyro integration.
- `PID_Control.h`: 10-sensor error calculation and PID differential drive speed calculation.
- `MotorDriver.h`: L298N PWM motor driving (direction and speed mapping).
- `DisplayUI.h`: 0.96" SSD1306 OLED update functions.
- `SerialComms.h`: Packet receiver/transmitter parser for Pi communication.

### Raspberry Pi Core Target (`v2_pi_core/`)
- `main.py`: Main state machine orchestrating vision, comms, and decisions.
- `config.py`: Video device, serial port settings, camera perspective warp matrix parameters, HSV thresholds.
- `comms/esp_bridge.py`: PySerial communication thread reading sensor states and sending motor/turn commands.
- `vision/camera_warp.py`: OpenCV perspective transformation logic for 20° camera tilt.
- `vision/green_dot.py`: HSV filtering, contour analysis, and green dot spatial positioning relative to line.
- `navigation/state_machine.py`: High-level navigation logic (Normal Line, Green Dot Turn, Obstacle Avoidance).
