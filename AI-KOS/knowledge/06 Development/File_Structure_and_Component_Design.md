# File Structure and Component Design Blueprints

## 1. Architectural Directory Layout

This blueprint defines the modular code structure to be generated for the DPSI-LFR V2 platform. Code is strictly segregated between hard real-time C++ firmware (`v2_esp32_firmware/`) and high-level Python application logic (`v2_pi_core/`).

```
DPSI-LFR/
├── v2_esp32_firmware/               # ESP32-S3 FreeRTOS Firmware Directory
│   ├── v2_esp32_firmware.ino        # Main entry point, FreeRTOS task spawner, setup/loop
│   ├── Config.h                     # Hardware GPIO mappings, system constants, pin macros
│   ├── IMU_Task.h                   # MPU6050 FreeRTOS Core 0 task interface & gyro integration
│   ├── LinePID.h                    # 10-Sensor digital reading, weighted error & PID math
│   ├── MotorDriver.h                # L298N dual-channel PWM LEDC driver abstraction
│   ├── SerialComms.h                # Binary serial packet parser & frame builder
│   └── DisplayUI.h                  # SSD1306 OLED graphics telemetry renderer
│
└── v2_pi_core/                      # Raspberry Pi 4B Python Core Navigation System
    ├── main.py                      # Master FSM execution thread, video loop, exception handling
    ├── config.py                    # Global vision thresholds, serial paths, system constants
    ├── comms/
    │   ├── __init__.py
    │   └── esp_bridge.py            # PySerial wrapper, packet framing, CRC16 calculation, thread lock
    ├── vision/
    │   ├── __init__.py
    │   ├── camera_warp.py           # OpenCV 20-degree homography matrix warp & rectification
    │   └── green_dot.py             # HSV thresholding, contour extraction, spatial decision logic
    └── navigation/
        ├── __init__.py
        └── state_machine.py         # Navigation state handlers (LineFollow, Turn90, Avoidance)
```

---

## 2. Firmware Component Contracts (`v2_esp32_firmware/`)

### 2.1 `Config.h`
- **Responsibility**: System-wide macro definitions, pin assignments, queue depth sizes, and operational parameters.
- **Key Definitions & Constants**:
  ```cpp
  // Hardware GPIO Mappings
  #define PIN_IR_1          1
  #define PIN_IR_2          2
  #define PIN_IR_3          4
  #define PIN_IR_4          5
  #define PIN_IR_5          6
  #define PIN_IR_6          7
  #define PIN_IR_7          15
  #define PIN_IR_8          16
  #define PIN_IR_9          17
  #define PIN_IR_10         18

  #define PIN_MOTOR_ENA     11
  #define PIN_MOTOR_IN1     12
  #define PIN_MOTOR_IN2     13
  #define PIN_MOTOR_IN3     14
  #define PIN_MOTOR_IN4     21
  #define PIN_MOTOR_ENB     47

  #define PIN_I2C_SDA       38
  #define PIN_I2C_SCL       39

  // System Constants
  #define SERIAL_BAUD_RATE  115200
  #define I2C_FREQ_HZ       400000
  #define PWM_FREQ_HZ       20000
  #define PWM_RESOLUTION_BITS 8
  ```

---

### 2.2 `IMU_Task.h`
- **Responsibility**: Manages MPU6050 hardware initialization on I2C, running continuous high-frequency background gyro integration pinned to FreeRTOS Core 0.
- **Data Structures**:
  ```cpp
  struct IMUData {
      float yaw;            // Integrated Z-axis heading angle in degrees
      float gyro_z_rad;     // Raw angular velocity in rad/sec
      bool is_calibrated;   // Calibration status flag
  };
  ```
- **Component Signatures**:
  - `bool initIMU(uint8_t sda_pin, uint8_t scl_pin)`: Initializes Wire library and configures MPU6050 registers ($\pm 250^\circ/\text{s}$ gyro scale). Returns `true` on success.
  - `void calibrateIMUGyro(uint16_t sample_count)`: Calculates Z-axis stationary zero-bias offset over specified samples.
  - `void Task_IMU_Polling(void* pvParameters)`: FreeRTOS task function (Infinite loop, pinned to Core 0, 200 Hz execution).
  - `float getIMUYaw()`: Thread-safe accessor function. Locks `g_imu_mutex` and returns latest integrated heading angle.

---

### 2.3 `LinePID.h`
- **Responsibility**: Reads 10x TCRT5000 digital inputs, computes weighted line position, calculates discrete PID outputs, and handles loss-of-line edge conditions.
- **Data Structures**:
  ```cpp
  struct PIDGains {
      float kp;
      float ki;
      float kd;
  };
  ```
- **Component Signatures**:
  - `void initLineSensors()`: Configures 10 IR GPIO pins as `INPUT_PULLUP`.
  - `uint16_t readIRSensorBitmask()`: Returns a 16-bit integer where bits 0-9 represent digital states of sensors 1-10.
  - `float calculateLineError(uint16_t bitmask, float& last_error)`: Computes weighted line position error ($e(t) \in [-9.0, +9.0]$).
  - `int16_t computePID(float current_error, PIDGains gains, float dt)`: Calculates PID output $u(t)$ bounded between $-255$ and $+255$.

---

### 2.4 `MotorDriver.h`
- **Responsibility**: Encapsulates ESP32-S3 LEDC hardware PWM generator channels and H-Bridge GPIO directional pins.
- **Component Signatures**:
  - `void initMotorDriver()`: Configures LEDC PWM timers and direction pins.
  - `void setMotorSpeeds(int16_t left_pwm, int16_t right_pwm)`: Sets individual wheel speeds ($[-255, +255]$). Handles forward/reverse H-bridge directional switching.
  - `void emergencyStopMotors()`: Instantly drives all directional pins LOW and sets PWM duty cycles to 0.

---

### 2.5 `SerialComms.h`
- **Responsibility**: Provides binary packet framing, byte stream decoding, CRC-16 computation, and command dispatching.
- **Data Structures**:
  ```cpp
  #pragma pack(push, 1)
  struct CommandPacket {
      uint8_t header1;     // 0xAA
      uint8_t header2;     // 0x55
      uint8_t seq_id;
      uint8_t opcode;
      uint8_t length;
      uint8_t payload[32];
      uint16_t crc16;
  };
  #pragma pack(pop)
  ```
- **Component Signatures**:
  - `uint16_t calculateCRC16(const uint8_t* data, uint16_t length)`: Computes CRC-16-CCITT checksum over frame bytes.
  - `bool parseIncomingByte(uint8_t byte_in, CommandPacket& out_packet)`: State-machine stream parser. Returns `true` when a complete valid packet is received.
  - `void sendTelemetryPacket(uint16_t ir_bitmask, float yaw, int16_t error)`: Formats and transmits telemetry frame over `Serial0`.

---

### 2.6 `DisplayUI.h`
- **Responsibility**: Renders diagnostic system information, IR sensor visualizers, and PID metrics onto the local SSD1306 OLED display.
- **Component Signatures**:
  - `bool initDisplay(uint8_t sda_pin, uint8_t scl_pin)`: Initializes Adafruit SSD1306 library instance over I2C (0x3C).
  - `void renderTelemetry(const char* mode_str, uint16_t ir_bitmask, float yaw, int16_t err, int16_t pwm_l, int16_t pwm_r)`: Draws formatted telemetry screens. Called at 10 Hz by `Task_OLED_Display`.

---

## 3. Python Component Contracts (`v2_pi_core/`)

### 3.1 `comms/esp_bridge.py`
- **Responsibility**: Thread-safe serial link manager providing high-level Python API methods for communicating with ESP32-S3.
- **Class Contract**: `class ESPBridge`
  - **Methods**:
    - `__init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200, timeout: float = 0.1)`: Opens serial port and initializes background RX reader thread.
    - `send_motor_speeds(self, left_pwm: int, right_pwm: int) -> bool`: Packs and sends `SET_MOTOR_SPEEDS` command.
    - `execute_turn_90(self, direction: str) -> bool`: Sends `EXECUTE_TURN_90` command (`direction` = `"LEFT"` or `"RIGHT"`).
    - `read_telemetry(self) -> dict`: Returns latest received telemetry dictionary (`{"ir_bitmask": int, "yaw": float, "error": int}`).
    - `close(self) -> None`: Safely releases serial resources and terminates background threads.

---

### 3.2 `vision/camera_warp.py`
- **Responsibility**: Handles video stream capture and inverse perspective transformation for camera tilt rectification.
- **Class Contract**: `class PerspectiveWarper`
  - **Methods**:
    - `__init__(self, src_pts: np.ndarray, dst_pts: np.ndarray, output_size: tuple = (400, 400))`: Computes homography matrix $M$ using `cv2.getPerspectiveTransform()`.
    - `warp(self, frame: np.ndarray) -> np.ndarray`: Applies perspective transformation via `cv2.warpPerspective()`. Returns rectified bird's-eye frame.

---

### 3.3 `vision/green_dot.py`
- **Responsibility**: Computer vision analyzer extracting green intersection markers and determining spatial navigation commands.
- **Class Contract**: `class GreenDotDetector`
  - **Methods**:
    - `__init__(self, hsv_lower: tuple, hsv_upper: tuple, min_area: int = 300)`: Stores HSV color bounds and noise filter thresholds.
    - `detect_dots(self, rectified_frame: np.ndarray) -> list[dict]`: Locates green contours and returns a list of dictionaries containing centroid coordinates `(x, y)` and bounding box areas.
    - `evaluate_intersection(self, dots: list, line_contour: np.ndarray) -> str`: Analyzes spatial positions of dots relative to main line contour. Returns command string (`"TURN_LEFT"`, `"TURN_RIGHT"`, `"U_TURN"`, `"NONE"`).

---

### 3.4 `navigation/state_machine.py`
- **Responsibility**: Implements the executive Finite State Machine (FSM) controlling autonomous mission workflow.
- **Class Contract**: `class NavigationMaster`
  - **Methods**:
    - `__init__(self, comms_bridge: ESPBridge, warper: PerspectiveWarper, detector: GreenDotDetector)`: Binds system dependencies and sets initial state to `LINE_FOLLOWING`.
    - `process_frame(self, frame: np.ndarray) -> None`: Evaluates incoming video frames, manages state transitions, and dispatches serial commands to ESP32-S3.
    - `set_state(self, new_state: str) -> None`: Manages entry and exit routines for state changes.
