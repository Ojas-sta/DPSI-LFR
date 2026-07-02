# Codebase Analysis Report: Hardware Migration to ESP32 DevKit V1

This report outlines all references to MPU6050, IR sensors, and motor pin configurations in the ESP32 diagnostics firmware that require refactoring or deletion.

---

## 1. MPU6050 / IMU References

### Observations
- A `grep_search` across the entire `src/` directory for `MPU` and `IMU` returned **zero** occurrences.
- `platformio.ini` does not include any third-party MPU6050 or IMU-related libraries.
- The project documentation (`PROJECT.md` and `knowledge/`) indicates that MPU6050 / IMU readings have been migrated to the Raspberry Pi.

### Conclusion
No code refactoring is needed for MPU6050/IMU as the driver and dependencies have already been removed from the C++ sources.

---

## 2. IR Sensor Array References

The 10-CH IR reflectance array logic and definitions are present across multiple files. These need to be removed completely as the IR sensors are deprecated in this firmware.

### 2.1 File: `src/Config.h`
- **Location**: Lines 25–36
- **Existing Code**:
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
- **Required Action**: Delete lines 25–36 entirely.

### 2.2 Files: `src/Sensors.h` and `src/Sensors.cpp`
- **Location**: Entire files
- **Existing Code**: Handles GPIO inputs and bitmask creation for the 10 IR sensors (`initSensors()`, `readIRSensorBitmask()`, `getIRSensorArray()`).
- **Required Action**: Delete both files (`src/Sensors.h` and `src/Sensors.cpp`) completely.

### 2.3 File: `src/Display.h`
- **Location**: Line 5
- **Existing Code**:
  ```cpp
  void updateDisplay(int clientCount, uint16_t irBitmask, int leftPWM, int rightPWM, bool watchdogOk);
  ```
- **Required Action**: Remove the `uint16_t irBitmask` parameter.
- **Proposed Signature**:
  ```cpp
  void updateDisplay(int clientCount, int leftPWM, int rightPWM, bool watchdogOk);
  ```

### 2.4 File: `src/Display.cpp`
- **Location**: Line 30 (Function Signature)
- **Existing Code**:
  ```cpp
  void updateDisplay(int clientCount, uint16_t irBitmask, int leftPWM, int rightPWM, bool watchdogOk) {
  ```
- **Required Action**: Update the signature to match the header.
- **Proposed Code**:
  ```cpp
  void updateDisplay(int clientCount, int leftPWM, int rightPWM, bool watchdogOk) {
  ```
- **Location**: Lines 45–48 (Display Rendering)
- **Existing Code**:
  ```cpp
  display.print("IR(HEX): 0x");
  if (irBitmask < 0x100) display.print("0");
  if (irBitmask < 0x10) display.print("0");
  display.println(irBitmask, HEX);
  ```
- **Required Action**: Delete lines 45–48 entirely.

### 2.5 File: `src/WebDiagnostics.h`
- **Location**: Line 7
- **Existing Code**:
  ```cpp
  void broadcastTelemetry(uint16_t irBitmask, uint8_t* irBits, int leftPWM, int rightPWM, bool watchdogOk);
  ```
- **Required Action**: Remove the `uint16_t irBitmask` and `uint8_t* irBits` parameters.
- **Proposed Signature**:
  ```cpp
  void broadcastTelemetry(int leftPWM, int rightPWM, bool watchdogOk);
  ```

### 2.6 File: `src/WebDiagnostics.cpp`
- **Location**: Line 56 (Function Signature)
- **Existing Code**:
  ```cpp
  void broadcastTelemetry(uint16_t irBitmask, uint8_t* irBits, int leftPWM, int rightPWM, bool watchdogOk) {
  ```
- **Required Action**: Update signature to match header.
- **Proposed Code**:
  ```cpp
  void broadcastTelemetry(int leftPWM, int rightPWM, bool watchdogOk) {
  ```
- **Location**: Lines 61–65 (Telemetry Payload Construction)
- **Existing Code**:
  ```cpp
  doc["ir_raw"] = irBitmask;
  JsonArray bits = doc.createNestedArray("ir_bits");
  for (int i=0; i<10; i++) {
      bits.add(irBits[i]);
  }
  ```
- **Required Action**: Delete lines 61–65.

### 2.7 File: `src/main.cpp`
- **Location**: Lines 47–48 (Telemetry Broadcast loop)
- **Existing Code**:
  ```cpp
  uint8_t dummy_bits[10] = {0};
  broadcastTelemetry(0, dummy_bits, getLeftMotorPWM(), getRightMotorPWM(), isWatchdogOk());
  ```
- **Required Action**: Modify the arguments passed to `broadcastTelemetry` to match the new signature.
- **Proposed Code**:
  ```cpp
  broadcastTelemetry(getLeftMotorPWM(), getRightMotorPWM(), isWatchdogOk());
  ```

### 2.8 File: `src/Dashboard.h`
- **Location**: Lines 35–39 (CSS styles)
- **Existing Code**:
  ```css
  /* IR Sensors */
  .ir-bar { display: flex; gap: 5px; justify-content: space-between; margin-top: 20px; }
  .ir-node { flex: 1; height: 40px; border-radius: 5px; background: #333; display: flex; align-items: center; justify-content: center; font-size: 0.8em; font-weight: bold; color: #777; transition: all 0.1s; border: 1px solid #222; }
  .ir-node.active { background: var(--accent); color: black; box-shadow: 0 0 10px var(--accent); border-color: white; }
  .ir-stats { margin-top: 15px; font-family: monospace; font-size: 1.1em; color: #aaa; text-align: center; }
  ```
- **Required Action**: Delete lines 35–39.

- **Location**: Lines 79–96 (HTML Card for IR Array)
- **Existing Code**:
  ```html
  <div class="card">
      <h2>10-CH IR Reflectance Array</h2>
      <div class="ir-bar" id="ir-container">
          <div class="ir-node" id="ir-0">IR1</div>
          ...
          <div class="ir-node" id="ir-9">IR10</div>
      </div>
      <div class="ir-stats">
          Bitmask: <span id="ir-hex" style="color: white">0x000</span> | DEC: <span id="ir-dec" style="color: white">0</span>
      </div>
  </div>
  ```
- **Required Action**: Delete lines 79–96.

- **Location**: Lines 137–143 (JS code parsing IR data)
- **Existing Code**:
  ```javascript
  // Update IR
  document.getElementById('ir-hex').textContent = '0x' + data.ir_raw.toString(16).padStart(3, '0').toUpperCase();
  document.getElementById('ir-dec').textContent = data.ir_raw;
  for (let i = 0; i < 10; i++) {
      document.getElementById('ir-' + i).className = data.ir_bits[i] ? 'ir-node active' : 'ir-node';
  }
  ```
- **Required Action**: Delete lines 137–143.

---

## 3. Motor and Peripheral Pin Migration

We must move the motor pins, reserve the analog inputs (ADC1), and move display pins to prevent pin configuration conflicts.

### 3.1 Motor Pins
- **File**: `src/Config.h` (Lines 11–18)
- **Existing Code**:
  ```cpp
  // Motor Control Pins (Grouped on the left side)
  #define PIN_MOTOR_ENA   13
  #define PIN_MOTOR_IN1   12
  #define PIN_MOTOR_IN2   11
  #define PIN_MOTOR_IN3   10
  #define PIN_MOTOR_IN4   3
  #define PIN_MOTOR_ENB   46
  ```
- **Required Action**: Move motor pins to the specified block (ENA=14, IN1=27, IN2=26, IN3=25, IN4=33, ENB=32).
- **Proposed Code**:
  ```cpp
  // Motor Control Pins (Grouped on the left side of ESP32 DevKit V1)
  #define PIN_MOTOR_ENA   14
  #define PIN_MOTOR_IN1   27
  #define PIN_MOTOR_IN2   26
  #define PIN_MOTOR_IN3   25
  #define PIN_MOTOR_IN4   33
  #define PIN_MOTOR_ENB   32
  ```

### 3.2 Reserved Analog Pins
- **File**: `src/Config.h` (to be added)
- **Required Action**: Add definitions for reserved input-only analog pins 34 and 35 (ADC1).
- **Proposed Code**:
  ```cpp
  // Reserved Analog Pins (ADC1, input-only pins on ESP32 DevKit V1)
  #define PIN_ANALOG_1    34
  #define PIN_ANALOG_2    35
  ```

### 3.3 I2C OLED Display Pins
- **File**: `src/Config.h` (Lines 37–39)
- **Existing Code**:
  ```cpp
  // I2C OLED Display
  #define PIN_I2C_SDA     35
  #define PIN_I2C_SCL     36
  ```
- **Required Action**: Move `PIN_I2C_SDA` and `PIN_I2C_SCL` to the hardware I2C pins of the ESP32 (SDA=21, SCL=22). Pin 35 is input-only on the ESP32 DevKit V1 and is reserved for analog input, meaning it cannot pull the SDA line low.
- **Proposed Code**:
  ```cpp
  // I2C OLED Display (Moved to standard ESP32 hardware I2C pins)
  #define PIN_I2C_SDA     21
  #define PIN_I2C_SCL     22
  ```

---

## 4. PlatformIO Configuration Updates

- **File**: `platformio.ini` (Lines 1–3)
- **Existing Code**:
  ```ini
  [env:esp32s3_diagnostics]
  platform = espressif32
  board = esp32-s3-devkitc-1
  ```
- **Required Action**: Change board target to `esp32doit-devkit-v1` and update environment name.
- **Proposed Code**:
  ```ini
  [env:esp32_diagnostics]
  platform = espressif32
  board = esp32doit-devkit-v1
  ```

---

## 5. Actionable Migration Plan

### Step 1: PlatformIO Target Update
- Modify `platformio.ini` to change the environment and target board from `esp32-s3-devkitc-1` to `esp32doit-devkit-v1`.

### Step 2: Config.h Pin Mapping
- Update `src/Config.h`:
  1. Replace the motor pin definitions with the new DevKit V1 GPIOs.
  2. Delete all `PIN_IR_x` sensor pin definitions.
  3. Move I2C OLED display pins from 35/36 to 21/22.
  4. Define `PIN_ANALOG_1` (34) and `PIN_ANALOG_2` (35) as reserved ADC1 inputs.

### Step 3: Deprecate Sensors Library files
- Completely delete `src/Sensors.h` and `src/Sensors.cpp`.

### Step 4: Refactor Display and WebSocket Telemetry Code
- Modify `src/Display.h` and `src/Display.cpp` to remove `irBitmask` and its printing logic.
- Modify `src/WebDiagnostics.h` and `src/WebDiagnostics.cpp` to remove `irBitmask` and `irBits` from `broadcastTelemetry` and from the JSON payload.
- Update `src/main.cpp` to call the refactored `broadcastTelemetry` function.
- Clean up `src/Dashboard.h` by deleting the IR reflectance HTML card, the IR sensor styles, and the corresponding WebSocket JavaScript handler.

### Step 5: Compile & Verify
- Run `pio run` to verify the codebase compiles successfully targeting the `esp32doit-devkit-v1` board.
