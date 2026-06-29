## 2026-06-29T08:11:23Z
<USER_REQUEST>
/goal

You are a Prompt Engineering Worker assigned to create the finalized Master Prompt for Claude Code inside `AI-KOS/prompts/Claude_Code_Prompt.md` for the DPSI-LFR V2 Differential Drive Robot.

IMPORTANT: Do NOT write any C++ (.cpp, .hpp, .ino) or Python (.py) code files! Your job is strictly to author the extensive markdown master prompt document `AI-KOS/prompts/Claude_Code_Prompt.md`.

Context & Technical Specs to Synthesize into the Master Prompt:
Read the newly authored blueprint files in `AI-KOS/knowledge/04 Architecture/` and `AI-KOS/knowledge/06 Development/` and `AI-KOS/shared-context/CurrentTask.md` to ensure complete consistency.
The prompt you construct will be given directly to Claude Code to generate the entire functional codebase for the V2 robot.

Requirements for `AI-KOS/prompts/Claude_Code_Prompt.md`:
1. System Role & Context: Instruct Claude Code that it is the Lead Firmware & Robotics Engineer implementing the code for DPSI-LFR V2.
2. Comprehensive Architecture Summary: Summarize the locked-in dual-brain hardware setup (Raspberry Pi 4B + ESP32-S3), exact GPIO pin assignments, L298N motor driver, 10x TCRT5000 IR array, MPU6050 IMU on FreeRTOS Core 0, SSD1306 OLED, 20° camera tilt perspective warp, and `/dev/ttyUSB0` serial protocol.
3. Target Directory & File Tree Instructions: Direct Claude Code to write code into two distinct target directories:
   - `v2_esp32_firmware/`: `v2_esp32_firmware.ino`, `Config.h`, `IMU_Task.h`, `PID_Control.h`, `MotorDriver.h`, `DisplayUI.h`, `SerialComms.h`.
   - `v2_pi_core/`: `main.py`, `config.py`, `comms/esp_bridge.py`, `vision/camera_warp.py`, `vision/green_dot.py`, `navigation/state_machine.py`.
4. Exact Implementation Guidelines for Each File:
   - For C++ files: provide step-by-step instructions for FreeRTOS task pinning (`xTaskCreatePinnedToCore`), task synchronization with mutexes/semaphores, discrete PID math over 10 digital sensors, zero-radius 90° pivot turns using gyro integration, L298N PWM motor channel mapping, OLED buffer rendering, and packet decoding/encoding.
   - For Python files: provide step-by-step instructions for OpenCV homography matrix setup (20° tilt rectification), HSV color thresholding & contour filtering for green dots, spatial decision logic relative to the main black line, PySerial binary packet frame handling with CRC verification, and multi-state FSM transitions.
5. Strict Formatting, Coding Standards & Testing Guidelines: Include rules for clean header guards, modular design, non-blocking loops, robust error recovery, and clear logging.
6. Execution Step-by-Step Instructions for Claude Code: Present the prompt in a structured, copy-paste ready format with clear execution phases for Claude Code.

Maintain your working directory in `.agents/worker_m2/`. Write your `progress.md` and deliver a detailed handoff report when completed. Remember: DO NOT write any C++ or Python code files! Deliver only `AI-KOS/prompts/Claude_Code_Prompt.md`.
</USER_REQUEST>
