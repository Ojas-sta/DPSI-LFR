# ESP32 Diagnostics Firmware Migration Plan

## Objectives
1. Migrate target board from `esp32-s3-devkitc-1` to `esp32doit-devkit-v1` in `platformio.ini`.
2. Move motor control pins to a sequential block on the left side of the ESP32:
   - `ENA`: GPIO 14
   - `IN1`: GPIO 27
   - `IN2`: GPIO 26
   - `IN3`: GPIO 25
   - `IN4`: GPIO 33
   - `ENB`: GPIO 32
3. Reserve analog pins:
   - `ANALOG_1`: GPIO 34 (ADC1)
   - `ANALOG_2`: GPIO 35 (ADC1)
4. Remove MPU6050 (IMU) and IR sensor definitions, logic, libraries, and tasks completely from the codebase.
5. Successfully compile the firmware using `pio run` in `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`.

## Steps
1. **Phase 1: Exploration**
   - Spawn an `explorer` subagent to perform codebase search, mapping out all references to MPU6050, IR sensors, and motor pins.
   - The explorer will generate an analysis report specifying the exact files and lines that need modification or deletion.

2. **Phase 2: Configuration & Pin Update**
   - Spawn a `worker` subagent to modify `platformio.ini` and `src/Config.h`.
   - Update board to `esp32doit-devkit-v1`.
   - Re-map motor pins and reserve analog pins.
   - Run compilation to see initial errors related to missing libraries/definitions.

3. **Phase 3: Sensor Removal & Cleanup**
   - Spawn a `worker` subagent to remove MPU6050 and IR sensor components.
   - Clean up `src/Sensors.cpp`, `src/Sensors.h`, `src/main.cpp`, `src/WebDiagnostics.cpp`, etc.
   - Verify that all dependent components compile without reference to the deleted sensor logic.

4. **Phase 4: Verification & Auditing**
   - Run `pio run` via the worker.
   - Spawn a `reviewer` subagent to verify code correctness and quality.
   - Spawn a `forensic auditor` to ensure that no cheating, hardcoded responses, or incomplete removals occurred.
