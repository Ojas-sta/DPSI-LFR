## 2026-06-30T06:58:30Z
/goal

You are the Worker subagent. Your mission is to implement Phase 2 of the hardware migration: configuration and pin configuration updates.

Working directory: `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/.agents/worker_config_migration`

Please execute the following tasks:
1. Update `platformio.ini`:
   - Change `board` to `esp32doit-devkit-v1`.
   - Update the environment block name from `esp32s3_diagnostics` to `esp32_diagnostics`.
2. Update `src/Config.h`:
   - Move motor control pins to the left-side block of ESP32 DevKit V1: ENA=14, IN1=27, IN2=26, IN3=25, IN4=33, ENB=32.
   - Add/reserve analog pins: `PIN_ANALOG_1` (34), `PIN_ANALOG_2` (35).
   - Relocate the I2C OLED display SDA and SCL pins: SDA=21, SCL=22.
   - Remove the `PIN_IR_1` to `PIN_IR_10` definitions entirely.
3. Try compiling using `pio run` to test these changes. Note that compilation might fail because we haven't removed the IR sensor logic from other source files yet, which is expected. Record the compilation output in your handoff report.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT
hardcode test results, create dummy/facade implementations, or
circumvent the intended task. A Forensic Auditor will independently
verify your work. Integrity violations WILL be detected and your
work WILL be rejected.

Write a detailed handoff report in your folder and send a message back to me when you are done.
