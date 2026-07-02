# Handoff Report - Explorer Subagent

This report outlines the findings, logic, and recommendations for migrating the ESP32 diagnostics firmware to the ESP32 DevKit V1 and removing the MPU6050 and IR sensors.

---

## 1. Observation

### 1.1 MPU6050 / IMU
A recursive case-insensitive search for `MPU` and `IMU` in `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/src` returned **no matches**. `platformio.ini` contains only web server, JSON, and display dependencies:
```ini
lib_deps =
    https://github.com/me-no-dev/ESPAsyncWebServer.git
    https://github.com/me-no-dev/AsyncTCP.git
    bblanchon/ArduinoJson @ ^6.21.3
    adafruit/Adafruit SSD1306 @ ^2.5.9
    adafruit/Adafruit GFX Library @ ^1.11.9
```
*Conclusion*: All MPU6050 logic has already been removed or deprecated from the C++ source files.

### 1.2 IR Sensor Array
The IR sensor logic is distributed across:
- **`src/Config.h` (Lines 25–36)**:
  ```cpp
  // IR Sensor Array Pins
  #define PIN_IR_1        1
  #define PIN_IR_2        2
  #define PIN_IR_3        4
  #define PIN_IR_4        5
  #define PIN_IR_5        6
  #define PIN_IR_6        7
  #define PIN_IR_7        15
  #define PIN_IR_8        16
  #define PIN_IR_9        17
  #define PIN_IR_10       18
  ```
- **`src/Sensors.h` & `src/Sensors.cpp` (All lines)**: Provides functions `initSensors()`, `readIRSensorBitmask()`, and `getIRSensorArray()`.
- **`src/Display.h` & `src/Display.cpp` (Lines 5, 30, 45–48)**: Passes `irBitmask` and prints it on the OLED display.
- **`src/WebDiagnostics.h` & `src/WebDiagnostics.cpp` (Lines 7, 56, 61–65)**: Packages `ir_raw` and `ir_bits` inside the WebSocket telemetry payload.
- **`src/main.cpp` (Lines 47–48)**: Creates a dummy array and passes it:
  ```cpp
  uint8_t dummy_bits[10] = {0};
  broadcastTelemetry(0, dummy_bits, ...);
  ```
- **`src/Dashboard.h` (Lines 35–39, 79–96, 137–143)**: CSS styling, HTML container, and JS parsing for the 10-CH IR array.

### 1.3 Motor Pin Configurations and I2C Display Pins
- **`src/Config.h` (Lines 11–18)**:
  ```cpp
  // Motor Control Pins (Grouped on the left side)
  #define PIN_MOTOR_ENA   13
  #define PIN_MOTOR_IN1   12
  #define PIN_MOTOR_IN2   11
  #define PIN_MOTOR_IN3   10
  #define PIN_MOTOR_IN4   3
  #define PIN_MOTOR_ENB   46
  ```
- **`src/Config.h` (Lines 37–39)**:
  ```cpp
  // I2C OLED Display
  #define PIN_I2C_SDA     35
  #define PIN_I2C_SCL     36
  ```

---

## 2. Logic Chain

1. **No MPU6050 logic exists in src**: Therefore, no driver, task, or setup code needs to be deleted or refactored for the IMU.
2. **IR Sensor Array Deprecation**:
   - The IR array is no longer used. Deleting `src/Sensors.h` and `src/Sensors.cpp` removes the physical reading logic.
   - Deleting the pin definitions from `src/Config.h` prevents compile issues or pin conflicts.
   - Removing the `irBitmask` parameters and usage in `src/Display.h/cpp`, `src/WebDiagnostics.h/cpp`, and `src/main.cpp` removes the references from the data/display pipeline.
   - Removing CSS, HTML structure, and JS WebSocket handling for `ir_raw` and `ir_bits` from `src/Dashboard.h` strips the IR reflectance display from the UI dashboard.
3. **ESP32 DevKit V1 Hardware Constraints**:
   - Standard ESP32 pins `34`, `35`, `36`, and `39` are **input-only** (ADC1/ADC2). They do not possess output buffers and cannot drive motors or act as I2C SDA (which requires bidirectional output capability).
   - The user requests:
     - Motor Pins: ENA=14, IN1=27, IN2=26, IN3=25, IN4=33, ENB=32 (these are all output-capable and safe to use).
     - Reserved Analog Pins: 34 and 35 (ADC1, input-only).
   - In `Config.h`, `PIN_I2C_SDA` was assigned to pin `35` and `PIN_I2C_SCL` to pin `36`. Since pin 35 is input-only and now reserved for analog readings, we must move I2C display pins.
   - Standard ESP32 hardware I2C pins are SDA=21, SCL=22. Moving `PIN_I2C_SDA` to `21` and `PIN_I2C_SCL` to `22` is electrical-safe and ensures the I2C OLED display operates correctly.

---

## 3. Caveats

- **I2C Pin Routing**: This migration assumes that standard hardware I2C pins `21` and `22` are free and wired to the OLED display on the ESP32 DevKit V1 board.
- **Library Compatibility**: We assume that the `Adafruit_SSD1306` library will correctly configure the moved I2C pins during `Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL)`.
- **PlatformIO versioning**: The standard compilation configuration uses standard libraries that support standard ESP32 architecture out-of-the-box.

---

## 4. Conclusion

To successfully migrate the diagnostic firmware to the target ESP32 DevKit V1:
1. Update `platformio.ini` board target to `esp32doit-devkit-v1`.
2. Move motor pin assignments in `Config.h` to the left-side block (14, 27, 26, 25, 33, 32).
3. Reserve analog inputs on pins 34 and 35.
4. Relocate OLED display I2C SDA and SCL pins to GPIO 21 and 22 to avoid input-only conflicts on pin 35.
5. Delete `Sensors.h` and `Sensors.cpp`.
6. Remove IR-related parameters and rendering code from `Display.h/cpp`, `WebDiagnostics.h/cpp`, `main.cpp`, and `Dashboard.h`.

---

## 5. Verification Method

### Automated Compile Test
Execute the following command in `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics`:
```bash
pio run
```
**Expected Result**: Compiles successfully (`[SUCCESS]`) and outputs a firmware binary.

### Codebase Auditing
- Verify that `src/Sensors.h` and `src/Sensors.cpp` are removed.
- Inspect `src/Config.h` to verify motor, display, and reserved analog pins match the DevKit V1 layout.
- Check `src/Dashboard.h` to ensure the HTML container for the IR array card is absent.
