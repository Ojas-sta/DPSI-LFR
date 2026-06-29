# Orchestrator Plan: DPSI-LFR V2 AI-KOS Architecture & Prompt Generation

## Objective
Orchestrate subagents to generate comprehensive AI-KOS planning documents, technical blueprints, architectural diagrams, task breakdowns, and the finalized master prompt for Claude Code to implement the DPSI-LFR V2 Differential Drive Robot.

## System Specs & Architecture (Locked-in)
- **Primary Brain**: Raspberry Pi 4B (Python OpenCV, 20° camera tilt, green dot intersection detection, high-level navigation/telemetry).
- **Microcontroller**: ESP32-S3 (C++ FreeRTOS, Core 0 for MPU6050 IMU heading integration, Core 1 for PID line following & motors).
- **Sensors**: 10x TCRT5000 IR sensors (single wide front array). MPU6050 IMU via I2C. Pi Camera angled 20° down.
- **Actuators & Drivers**: L298N motor driver controlling 2x 12V 600RPM DC motors in differential drive configuration.
- **Telemetry & UI**: 0.96-inch I2C OLED display on ESP32-S3 for debugging/status (no physical push buttons).
- **Inter-chip Communication**: USB Serial (`/dev/ttyUSB0` at 115200 baud) between Pi 4B and ESP32-S3.

## Work Breakdown Structure (Milestones)
- **Milestone 1**: Comprehensive Architectural Analysis & Blueprint Generation in `AI-KOS/knowledge/` and updated `AI-KOS/shared-context/CurrentTask.md`.
- **Milestone 2**: Finalized Claude Code Master Prompt Generation in `AI-KOS/prompts/Claude_Code_Prompt.md`.
- **Milestone 3**: Architectural Review, Verification & Audit of all deliverables.

## Execution Strategy
- All deliverables inside `AI-KOS/` will be written by dedicated worker subagents (`teamwork_preview_worker`).
- Independent verification and review will be performed by reviewer subagents (`teamwork_preview_reviewer`).
- Zero code files (`.cpp`, `.ino`, `.py`) will be generated.
