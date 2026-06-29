# Current Task: V2 Architecture First Codebase

## Objective
Generate the first functional codebase for the V2 Differential Drive Robot.

## Hardware & Geometry Specs (LOCKED IN)
- **Brains**: Raspberry Pi 4B + ESP32-S3 (Connected via USB Serial `/dev/ttyUSB0`)
- **Power**: LM2596 tuned to 5.1V for logic, 12V battery for motors.
- **Motors**: 2x 12V 600RPM DC Motors driven by an L298N.
- **Chassis Geometry**: 140mm Track Width (wheel-to-wheel). 180mm distance from Drive Axle to rear Caster.
- **Sensors**: 
  - **Line Following**: 10x TCRT5000 IR Sensors mounted as **one single wide line** across the front.
  - **Odometry**: MPU6050 IMU Gyro on the ESP32 (I2C) for exact 90-degree intersection turns.
  - **Vision**: Pi Camera angled **20 degrees down** (requires OpenCV perspective warp).
  - **Debugging/UI**: 0.96-inch I2C OLED Display wired to the ESP32-S3 for local debugging and telemetry display.

## Division of Labor
- **ESP32-S3 (Hard Real-Time)**
  - Runs a fast PID loop over the 10-bit wide IR sensor array for ultra-smooth line following.
  - Runs a dedicated **FreeRTOS task on Core 0** continuously polling and integrating the MPU6050 Z-axis gyro to maintain an exact heading.
  - Accepts `<L_SPEED>,<R_SPEED>` commands from the Pi.
  - Accepts `<TURN_90_LEFT>` commands from the Pi, at which point it uses the IMU to execute a perfect pivot turn.
  - Updates the 0.96" OLED with live sensor states and PID variables for debugging.

- **Raspberry Pi 4B (High-Level Logic)**
  - Reads camera frames, applies perspective warp for the 20-degree tilt.
  - Detects Green Dots at intersections using HSV filtering.
  - Detects obstacles and navigates the Rescue Zone.
  - Streams telemetry to a Web Dashboard.

## Required File Structure for Claude Code
**1. `v2_esp32_firmware/` (Arduino/C++)**
- `v2_esp32_firmware.ino`: Main setup and Core 1 loop (Line Following PID & Serial parsing).
- `IMU_Task.h`: FreeRTOS task pinned to Core 0 that handles the MPU6050.
- `Config.h`: GPIO mappings for L298N (ENA, IN1, IN2, IN3, IN4, ENB), 10x IR sensors, and I2C (SDA/SCL) for the OLED and MPU6050.
- `DisplayUI.h`: Manages drawing telemetry to the 0.96" OLED.

**2. `v2_pi_core/` (Python)**
- `main.py`: Main state machine.
- `comms/esp_bridge.py`: PySerial interface to `/dev/ttyUSB0`.
- `vision/camera_warp.py`: OpenCV perspective transformation logic.
- `vision/green_dot.py`: Intersection logic.
