# Original User Request

## Initial Request — 2026-06-30T12:19:54Z

/goal

# Teamwork Project Prompt

Refactor the ESP32 diagnostics firmware to target the ESP32 DevKit V1, executing the hardware migration exactly as detailed in the implementation plan.

Working directory: /Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics
Integrity mode: development

## Requirements

### R1. PlatformIO Configuration
Update `platformio.ini` to change the board target to `esp32doit-devkit-v1`.

### R2. Hardware Configuration
Update `Config.h` and the codebase to:
- Move motor pins to the left-side block: ENA=14, IN1=27, IN2=26, IN3=25, IN4=33, ENB=32.
- Reserve analog pins 34 and 35 (ADC1).
- Ensure any logic or definitions for the MPU6050 and IR sensors are entirely removed.

### R3. Safe Execution
Read the `implementation_plan.md` artifact to understand the exact context before modifying the codebase. 

## Acceptance Criteria

### Compilation
- [ ] The firmware successfully compiles for the new architecture when running `pio run` in the working directory with 0 errors.
