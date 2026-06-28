---
file: CurrentTask.md
purpose: The single actively-in-progress task — what is being worked on right now
last_updated: 2026-06-29T02:45:00+05:30
updated_by: Antigravity
version: 2.0.0
---

## Purpose

This file tracks the ONE task currently being worked on. Only one task may be
active at a time per agent. Update this file when you start, make progress on,
or complete a task.

## Content

### Task

| Field | Value |
|-------|-------|
| Task ID | V2-001 |
| Title | Implement DPSI-LFR V2 Architecture Blueprint |
| Description | Migrate DPSI-LFR to dual-brain architecture (ESP32-S3 + Raspberry Pi 4B) based on implementation plan. Includes creating file structures, C++ classes for ESP32, and Python modules for Pi. |
| Assigned Agent | Builder (Claude Code) |
| Status | 🟢 Ready for generation |
| Started | 2026-06-29T02:40:00+05:30 |
| Dependencies | None |
| Blocks | V2-002 (Testing Firmware) |

### Technical Blueprint & Subtasks

**1. `v2_esp32_firmware/` (C++ Firmware)**
- [ ] `v2_esp32_firmware.ino`: Main setup and loop routines.
- [ ] `Config.h`: Define GPIO pins (Motor L: 4,5,6 / Motor R: 7,15,16 / Front Array: 8,9,10,11,12 / Secondary Array: 13,14,17,18,21).
- [ ] `MotorDriver.h/cpp`: Class `DifferentialMotorDriver` with `setSpeeds(leftSpeed, rightSpeed)`.
- [ ] `SensorArray.h/cpp`: Class `IRSensorArray` with `readAll()` returning 10-bit state from the two TCRT5000 arrays.
- [ ] `SerialBridge.h/cpp`: Class `PiBridge` for packet parsing (`<L_SPEED>,<R_SPEED>\n` receiving, `<S1_1>...<S2_5>\n` sending).

**2. `v2_pi_core/` (Python High-Level)**
- [ ] `main.py`: Entry point for high-level Pi logic, initializing comms, vision, and control.
- [ ] `comms/esp_bridge.py`: Class `ESP32Bridge` handling UART0 over USB to the ESP32.
- [ ] `vision/camera.py`: Class `PiCamera` wrapping OpenCV video capture and frame formatting.
- [ ] `vision/detector.py`: Class `LineDetector` for visual processing (e.g. contour detection).
- [ ] `control/pid_controller.py`: Class `PIDController` for line following error correction.
- [ ] `control/state_manager.py`: Class `RobotStateManager` bridging vision, sensor data, and motor commands.

### Notes

- **Architecture Change:** Avoid Mecanum kinematics in V2. We are moving strictly to differential drive.
- **Pinout:** Refer to `implementation_plan.md` for specific pinouts (avoiding PSRAM, USB, and Strapping Pins).

### Files to Create/Modify
- `v2_esp32_firmware/*`
- `v2_pi_core/*`
