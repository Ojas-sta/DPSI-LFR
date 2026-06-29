# Orchestrator Context

## Project Summary
DPSI-LFR V2 is a differential drive line following and maze solving robot built on a dual-controller architecture (Raspberry Pi 4B + ESP32-S3).

## Hardware Constraints & Protocol Rules
- **ESP32-S3**: Dual core microcontroller running FreeRTOS.
  - Core 0: Continuous MPU6050 IMU polling and Z-axis integration for yaw angle and precision turning.
  - Core 1: 10x TCRT5000 IR array digital pin reads, high-frequency PID control loop, L298N PWM motor driving, OLED status display, Serial packet processing.
- **Raspberry Pi 4B**: Linux computer running Python OpenCV vision and high-level state machine.
  - Pi Camera with 20° tilt forward down. Inverse perspective mapping (perspective warp) to rectify image plane.
  - Green Dot detection via HSV color thresholding & contour analysis for intersection decision-making (Rescue / Line Follow maze rules).
- **Serial Protocol**: Custom lightweight binary/text packet structure over USB Serial `/dev/ttyUSB0` (115200 baud).

## Deliverable Scope
All work must be markdown documents placed within `AI-KOS/` directory. No source code binaries or `.cpp`/`.py` code implementations are to be written in this phase.
