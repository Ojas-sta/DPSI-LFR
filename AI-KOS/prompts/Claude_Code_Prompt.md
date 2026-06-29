# MASTER PROMPT: DPSI-LFR V2 Differential Drive Autonomous Robot Implementation

> **PROMPT INSTRUCTIONS FOR CLAUDE CODE**:
> You are to act as the **Lead Firmware & Robotics Engineer** tasked with implementing the complete, production-ready source code for the **DPSI-LFR V2 Autonomous Line-Following & Rescue Robot**.
> Read this entire document carefully. Execute the implementation phase-by-phase according to the specified file contracts, algorithms, pinouts, and protocols. Do not skip any files or implementation details.

---

## 1. System Role & Context

You are operating as the **Lead Firmware & Robotics Engineer** within the AI-KOS ecosystem. Your objective is to write the full implementation code for the DPSI-LFR V2 robot.
The DPSI-LFR V2 is a dual-brain differential drive robot designed for competitive autonomous navigation, high-speed line following, green-dot intersection handling, deterministic obstacle avoidance, and rescue zone navigation.

The software architecture is decoupled into two primary domain execution tiers:
1. **Hard Real-Time Microcontroller Tier (`v2_esp32_firmware/`)**: Executed on an **ESP32-S3** dual-core MCU under **FreeRTOS** in C++ Arduino framework. Handles sensor high-frequency sampling (10-sensor IR array, MPU6050 IMU gyro integration), 100Hz discrete PID line-following calculations, closed-loop 90° pivot turning, L298N motor PWM generation, and SSD1306 OLED telemetry rendering.
2. **High-Level Computer Vision & Intelligence Tier (`v2_pi_core/`)**: Executed on a **Raspberry Pi 4B** in Python 3 with OpenCV and PySerial. Handles camera frame capture, 20° tilt inverse perspective transformation, HSV color segmentation and contour analysis for green dot intersection navigation, high-level Finite State Machine (FSM) control, and serial command bridging.

---

## 2. Comprehensive Architecture & Hardware Specifications

### 2.1 Dual-Brain Hardware Overview & Subsystem Allocation
- **Microcontroller**: ESP32-S3 (Xtensa 32-bit LX7 dual-core @ 240MHz, 512KB SRAM, 8MB Flash).
- **Primary Brain**: Raspberry Pi 4B (Quad-core ARM Cortex-A72 @ 1.5GHz, 4GB/8GB RAM).
- **Communication Bridge**: Full-duplex USB Serial (`/dev/ttyUSB0` on Pi 4B mapped to UART0 `GPIO43/GPIO44` on ESP32-S3) at **115,200 baud** (8N1) with binary frame packing and CRC-16-CCITT validation.
- **Power Architecture**: 12V LiPo battery rail directly powering L298N H-Bridge VMS input. LM2596 DC-DC Buck converter tuned strictly to **5.10V $\pm 0.05\text{V}$** supplying Raspberry Pi 4B and ESP32-S3 VIN. Single star-ground topology at the L298N power terminal block.

### 2.2 ESP32-S3 GPIO Pin Assignment Matrix

| Subsystem / Peripheral | Function / Signal Name | ESP32-S3 Pin | Signal Type | Electrical / Operational Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **IR Array (TCRT5000)** | Sensor 1 (Far Left) | `GPIO1` | Digital Input | Pulled LOW on reflection (Black line = HIGH) |
| **IR Array (TCRT5000)** | Sensor 2 | `GPIO2` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 3 | `GPIO4` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 4 | `GPIO5` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 5 (Center Left)| `GPIO6` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 6 (Center Right)| `GPIO7` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 7 | `GPIO15` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 8 | `GPIO16` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 9 | `GPIO17` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 10 (Far Right)| `GPIO18` | Digital Input | Pulled LOW on reflection |
| **L298N Motor Driver** | ENA (Left Speed PWM) | `GPIO11` | LEDC PWM Out | 20 kHz PWM frequency, 8-bit resolution |
| **L298N Motor Driver** | IN1 (Left Dir A) | `GPIO12` | Digital Out | Direction logic (HIGH/LOW) |
| **L298N Motor Driver** | IN2 (Left Dir B) | `GPIO13` | Digital Out | Direction logic (LOW/HIGH) |
| **L298N Motor Driver** | IN3 (Right Dir A) | `GPIO14` | Digital Out | Direction logic (HIGH/LOW) |
| **L298N Motor Driver** | IN4 (Right Dir B) | `GPIO21` | Digital Out | Direction logic (LOW/HIGH) |
| **L298N Motor Driver** | ENB (Right Speed PWM)| `GPIO47` | LEDC PWM Out | 20 kHz PWM frequency, 8-bit resolution |
| **I2C Bus (Shared)** | SDA (Serial Data) | `GPIO38` | I2C Data | 400 kHz Fast-Mode, shared by SSD1306 & MPU6050 |
| **I2C Bus (Shared)** | SCL (Serial Clock) | `GPIO39` | I2C Clock | 400 kHz Fast-Mode I2C Clock |
| **Serial Communication** | UART TX (`TXD0`) | `GPIO43` | UART Output | Connected to Pi 4B (`/dev/ttyUSB0`) |
| **Serial Communication** | UART RX (`RXD0`) | `GPIO44` | UART Input | Connected to Pi 4B (`/dev/ttyUSB0`) |

### 2.3 Physical Geometry & Kinematics Specification
- **Track Width ($W$)**: $140\text{ mm} = 0.140\text{ m}$ (distance between wheel centerlines).
- **Wheel Diameter ($D_w$)**: $65\text{ mm} = 0.065\text{ m}$ (radius $R = 0.0325\text{ m}$).
- **Wheelbase ($L_{caster}$)**: $180\text{ mm} = 0.180\text{ m}$ (axle to passive rear caster).
- **Motors**: 2x 12V DC Gear Motors, 600 RPM max unloaded speed ($\approx 2.04\text{ m/s}$ max velocity).
- **Forward Kinematics**: Linear velocity $v = (v_R + v_L)/2$; Angular velocity $\omega = (v_R - v_L)/W$.
- **Inverse Kinematics**: Wheel velocities $v_L = v - \frac{\omega W}{2}$, $v_R = v + \frac{\omega W}{2}$.
- **Zero-Radius Pivot Turn**: When $v_L = -v_R$, net linear speed $v = 0$ and Instantaneous Center of Rotation $R_{ICR} = 0$.

### 2.4 Binary Serial Protocol Specification
All transactions over UART operate using binary structured frames with header `0xAA 0x55` and CRC-16-CCITT polynomial ($X^{16} + X^{12} + X^5 + 1$, seed `0xFFFF`).

**Binary Frame Structure**:
`[0xAA (1B)] [0x55 (1B)] [Seq_ID (1B)] [Opcode (1B)] [Payload_Length N (1B)] [Payload (N Bytes)] [CRC16_Low (1B)] [CRC16_High (1B)]`

**Opcodes Table**:
- `0x01` (`SET_MOTOR_SPEEDS`, Pi $\to$ ESP): Payload 4B (`int16_t left_pwm`, `int16_t right_pwm`). Direct motor control override.
- `0x02` (`EXECUTE_TURN_90`, Pi $\to$ ESP): Payload 1B (`uint8_t direction`: `0x01`=Left, `0x02`=Right). Closed-loop IMU pivot turn.
- `0x03` (`EXECUTE_TURN_180`, Pi $\to$ ESP): Payload 0B. IMU-guided 180° U-turn.
- `0x04` (`SET_PID_GAINS`, Pi $\to$ ESP): Payload 12B (`float kp`, `float ki`, `float kd`). Dynamically update PID gains.
- `0x05` (`SET_MODE`, Pi $\to$ ESP): Payload 1B (`uint8_t mode`: `0`=Standby, `1`=LineFollow, `2`=Manual).
- `0x0A` (`HEARTBEAT_PING`, Pi $\to$ ESP): Payload 1B (`uint8_t status`). Sent every 200ms to reset safety watchdog.
- `0xFF` (`EMERGENCY_STOP`, Pi $\to$ ESP): Payload 0B. Cuts power to L298N motors immediately.
- `0x81` (`REPORT_TELEMETRY`, ESP $\to$ Pi): Payload 10B (`uint16_t ir_bitmask`, `float yaw`, `int16_t error`). Broadcast at 20 Hz.
- `0x82` (`TURN_COMPLETE`, ESP $\to$ Pi): Payload 2B (`uint8_t turn_type`, `uint8_t status`). Sent on completing IMU turn within deadband.
- `0x8A` (`HEARTBEAT_PONG`, ESP $\to$ Pi): Payload 2B (`uint16_t uptime_sec`). Health response.
- `0xFE` (`ACK_COMMAND`, ESP $\to$ Pi): Payload 2B (`uint8_t rx_seq_id`, `uint8_t rx_opcode`). Frame acknowledgment.
- `0xFF` (`ERROR_REPORT`, ESP $\to$ Pi): Payload 2B (`uint8_t error_code`, `uint8_t detail_code`). CRC or watchdog alert.

---

## 3. Target Directory Structure & File Tree

Direct Claude Code to construct the entire software tree across two distinct project directories:

```
DPSI-LFR/
├── v2_esp32_firmware/               # ESP32-S3 FreeRTOS C++ Firmware Directory
│   ├── v2_esp32_firmware.ino        # Main entry point, FreeRTOS task spawner, setup/loop
│   ├── Config.h                     # Hardware GPIO mappings, system constants, pin macros
│   ├── IMU_Task.h                   # MPU6050 FreeRTOS Core 0 task interface & gyro integration
│   ├── PID_Control.h                # 10-Sensor digital reading, weighted error & PID math
│   ├── MotorDriver.h                # L298N dual-channel PWM LEDC driver abstraction
│   ├── DisplayUI.h                  # SSD1306 OLED graphics telemetry renderer
│   └── SerialComms.h                # Binary serial packet parser & frame builder
│
└── v2_pi_core/                      # Raspberry Pi 4B Python Navigation Core System
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
        └── state_machine.py         # Navigation state handlers (LineFollow, Turn90, Avoidance, Rescue)
```

---

## 4. Exact Implementation Guidelines for Each Component File

### 4.1 Firmware Component Specifications (`v2_esp32_firmware/`)

#### 1. `Config.h`
- **Header Guards**: `#ifndef CONFIG_H_` / `#define CONFIG_H_`
- **GPIO Pin Definitions**: Define all macros for IR array (`PIN_IR_1` to `PIN_IR_10`), L298N pins (`PIN_MOTOR_ENA`, `PIN_MOTOR_IN1`..`IN4`, `PIN_MOTOR_ENB`), I2C (`PIN_I2C_SDA=38`, `PIN_I2C_SCL=39`), UART (`PIN_UART_TX=43`, `PIN_UART_RX=44`).
- **LEDC PWM Parameters**: `PWM_FREQ_HZ = 20000`, `PWM_RESOLUTION_BITS = 8`, `LEDC_CHANNEL_LEFT = 0`, `LEDC_CHANNEL_RIGHT = 1`.
- **Operating Constants**: Baud rate `115200`, I2C freq `400000`, Watchdog timeout `500ms`, PID loop period `10ms` (100 Hz), IMU period `5ms` (200 Hz), OLED period `100ms` (10 Hz).

#### 2. `IMU_Task.h`
- **Dependencies**: `<Wire.h>`, FreeRTOS headers.
- **Data Structures**: `struct IMUData { float yaw; float gyro_z_rad; bool is_calibrated; };`
- **FreeRTOS Synchronization**: Declare global mutex `SemaphoreHandle_t g_imu_mutex` and global variable `float g_current_yaw`.
- **Functions**:
  - `bool initIMU(uint8_t sda, uint8_t scl)`: Initializes MPU6050 over I2C at address `0x68`. Sets gyro full-scale range to $\pm 250^\circ/\text{s}$.
  - `void calibrateIMUGyro(uint16_t samples)`: Takes stationary readings to compute Z-axis zero bias `gz_offset`.
  - `void Task_IMU_Polling(void* pvParameters)`: Pinned to **Core 0**, Priority 5, 200 Hz loop (`vTaskDelayUntil`). Reads raw gyro Z, subtracts offset, integrates yaw: $g\_current\_yaw += (g_z - offset) \times \Delta t$. Protects write access with `xSemaphoreTake(g_imu_mutex, portMAX_DELAY)`.
  - `float getIMUYaw()`: Thread-safe getter returning latest yaw angle.

#### 3. `PID_Control.h`
- **Dependencies**: `Config.h`.
- **Data Structures**: `struct PIDGains { float kp; float ki; float kd; };`
- **Sensors & Error Calculation**:
  - `void initLineSensors()`: Configures 10 IR GPIO pins as `INPUT_PULLUP`.
  - `uint16_t readIRSensorBitmask()`: Reads 10 IR pins; returns 10-bit integer mask. (`1` = black line detected, `0` = white).
  - `float calculateLineError(uint16_t bitmask, float& last_error)`: Assigns symmetric weights $W = [-9, -7, -5, -3, -1, +1, +3, +5, +7, +9]$. Computes weighted center of gravity position $P_{line} = \frac{\sum (S_i \cdot W_i)}{\sum S_i}$.
  - **Loss of Line Handling**: If $\sum S_i == 0$, return inflated error $\pm 12.0$ matching sign of `last_error`.
  - `int16_t computePID(float error, PIDGains gains, float dt)`: Computes $P = K_p \cdot e$, $I = \text{clamp}(I + K_i \cdot e \cdot dt, -50, +50)$, $D = K_d \cdot \frac{e - e_{prev}}{dt}$. Returns output $u(t)$ constrained between $-255$ and $+255$.

#### 4. `MotorDriver.h`
- **Dependencies**: `Config.h`, `driver/ledc.h` (or Arduino `ledcAttachChannel` / `ledcWrite`).
- **Functions**:
  - `void initMotorDriver()`: Attaches PWM pins to LEDC channels at 20 kHz 8-bit resolution. Sets direction pins (`IN1..IN4`) as `OUTPUT`.
  - `void setMotorSpeeds(int16_t left_pwm, int16_t right_pwm)`: Clamps inputs to $[-255, +255]$. For positive values, sets direction for forward spin. For negative values, sets reverse direction for active braking/counter-rotation. Writes absolute PWM value to LEDC channel.
  - `void emergencyStopMotors()`: Sets PWM duty to 0 and all directional pins LOW.

#### 5. `SerialComms.h`
- **Dependencies**: `<Arduino.h>`, `Config.h`, FreeRTOS queues.
- **Structures**: Declare `#pragma pack(push, 1)` packed structures for `CommandPacket` and telemetry frames.
- **FreeRTOS Queue**: Declare global queue `QueueHandle_t g_command_queue` (depth 10).
- **Functions**:
  - `uint16_t calculateCRC16(const uint8_t* data, uint16_t length)`: Standard CRC-16-CCITT implementation.
  - `bool parseIncomingByte(uint8_t byte_in, CommandPacket& out_packet)`: State machine byte stream parser (`WAIT_H1`, `WAIT_H2`, `READ_SEQ`, `READ_OPCODE`, `READ_LEN`, `READ_PAYLOAD`, `READ_CRC1`, `READ_CRC2`). Validates CRC upon frame completion.
  - `void sendTelemetryPacket(uint16_t bitmask, float yaw, int16_t error)`: Packs `REPORT_TELEMETRY` opcode `0x81`, calculates CRC16, and writes binary frame to `Serial`.

#### 6. `DisplayUI.h`
- **Dependencies**: `<Adafruit_GFX.h>`, `<Adafruit_SSD1306.h>`.
- **Functions**:
  - `bool initDisplay(uint8_t sda, uint8_t scl)`: Initializes SSD1306 display at I2C address `0x3C` ($128 \times 64$).
  - `void renderTelemetry(const char* mode_str, uint16_t bitmask, float yaw, int16_t err, int16_t pwm_l, int16_t pwm_r)`: Draws 4-row structured telemetry interface (Row 0-15: Mode & Battery status; Row 16-31: 10 IR solid/empty indicator boxes; Row 32-47: Integrated Yaw and PID Error; Row 48-63: Motor PWM outputs). Runs at 10 Hz non-blocking.

#### 7. `v2_esp32_firmware.ino`
- **Main Setup & FreeRTOS Task Spawner**:
  - Initializes Serial at 115200 baud. Initializes I2C (`Wire.begin(38, 39, 400000)`).
  - Initializes hardware peripherals (`initMotorDriver()`, `initLineSensors()`, `initIMU()`, `initDisplay()`).
  - Creates synchronization primitives: `g_imu_mutex = xSemaphoreCreateMutex()`, `g_command_queue = xQueueCreate(10, sizeof(CommandPacket))`.
  - Spawns FreeRTOS tasks:
    - `Task_IMU_Polling`: Pinned to **Core 0**, Priority 5, stack 4096.
    - `Task_LineFollow_PID`: Pinned to **Core 1**, Priority 4, stack 8192.
    - `Task_Serial_Parser`: Pinned to **Core 1**, Priority 3, stack 4096.
    - `Task_OLED_Display`: Pinned to **Core 1**, Priority 1, stack 3072.
- **Task Implementation Highlights**:
  - `Task_LineFollow_PID`: Implements state machine (`MODE_STANDBY`, `MODE_LINE_FOLLOW`, `MODE_IMU_TURN`). Checks `g_last_packet_timer` against 500ms safety watchdog threshold. In `MODE_IMU_TURN`, executes closed-loop pivot turn using IMU feedback until target angle ($\pm 90^\circ$) is reached within $\pm 0.5^\circ$ deadband, executes 20ms reverse brake pulse, and transmits `TURN_COMPLETE` packet (`0x82`).

---

### 4.2 Python Computer Vision & Navigation Specifications (`v2_pi_core/`)

#### 1. `config.py`
- **Constants**:
  - Serial port: `SERIAL_PORT = "/dev/ttyUSB0"`, `BAUD_RATE = 115200`.
  - Camera settings: `FRAME_WIDTH = 640`, `FRAME_HEIGHT = 480`, `FPS = 30`.
  - Perspective Homography coordinates:
    `SRC_POINTS = np.float32([[180, 260], [460, 260], [600, 460], [40, 460]])`
    `DST_POINTS = np.float32([[0, 0], [400, 0], [400, 400], [0, 400]])`
  - HSV Color Bounds:
    `GREEN_LOWER = np.array([35, 80, 80])`, `GREEN_UPPER = np.array([85, 255, 255])`
    `BLACK_LOWER = np.array([0, 0, 0])`, `BLACK_UPPER = np.array([180, 255, 50])`
  - Contour area thresholds: `GREEN_MIN_AREA = 300`, `GREEN_MAX_AREA = 5000`.

#### 2. `comms/esp_bridge.py`
- **Class `ESPBridge`**:
  - Thread-safe `pyserial` interface. Background thread reads binary incoming frames from ESP32-S3, calculates CRC16, and stores telemetry.
  - `send_packet(opcode: int, payload: bytes)`: Formats frame `[0xAA, 0x55, seq, opcode, len, payload, crc_low, crc_high]` and writes to serial port under thread lock.
  - `send_motor_speeds(left_pwm: int, right_pwm: int)`: Opcode `0x01`.
  - `execute_turn_90(direction: str)`: Opcode `0x02` (`direction` `"LEFT"` $\to$ `0x01`, `"RIGHT"` $\to$ `0x02`).
  - `execute_turn_180()`: Opcode `0x03`.
  - `send_heartbeat()`: Opcode `0x0A`.
  - `read_telemetry()`: Returns dictionary of latest telemetry.

#### 3. `vision/camera_warp.py`
- **Class `PerspectiveWarper`**:
  - `__init__(src_pts, dst_pts, output_size=(400, 400))`: Computes $3 \times 3$ Homography matrix using `cv2.getPerspectiveTransform(src_pts, dst_pts)`.
  - `warp(frame)`: Applies `cv2.warpPerspective(frame, self.M, self.output_size)`. Returns rectified bird's-eye frame.

#### 4. `vision/green_dot.py`
- **Class `GreenDotDetector`**:
  - `detect_dots(rectified_frame)`: Converts frame to HSV. Applies `cv2.inRange()` with green lower/upper bounds. Applies morphological `MORPH_OPEN` and `MORPH_CLOSE` with $5 \times 5$ ellipse kernel. Extracts external contours with `cv2.findContours()`. Filters by area ($300 \le A \le 5000$). Computes contour moments (`cv2.moments`) to find spatial centroid $(\bar{x}, \bar{y})$.
  - `evaluate_intersection(dots, line_contour)`: Compares green dot centroids to main black line bounding box centroid $x_{line}$.
    - Green dot to left ($\bar{x} < x_{line} - \delta$): Returns `"TURN_LEFT"`.
    - Green dot to right ($\bar{x} > x_{line} + \delta$): Returns `"TURN_RIGHT"`.
    - Green dots on both sides: Returns `"U_TURN"`.
    - Otherwise: Returns `"NONE"`.

#### 5. `navigation/state_machine.py`
- **Class `NavigationMaster`**:
  - Implements executive Finite State Machine with states: `STATE_LINE_FOLLOWING`, `STATE_INTERSECTION_DECISION`, `STATE_OBSTACLE_AVOIDANCE`, `STATE_RESCUE_ZONE_NAVIGATION`.
  - `process_frame(frame)`: Warps frame, extracts green dots and line contours.
  - In `STATE_LINE_FOLLOWING`: Monitors markers. If intersection detected, transitions to `STATE_INTERSECTION_DECISION`. Sends periodic heartbeat ping every 200ms.
  - In `STATE_INTERSECTION_DECISION`: Overrides line following by issuing `execute_turn_90` or `execute_turn_180`. Waits asynchronously for `TURN_COMPLETE` telemetry packet before transitioning back to `STATE_LINE_FOLLOWING`.

#### 6. `main.py`
- Main entry point script. Initializes OpenCV video capture (`cv2.VideoCapture(0)`). Instantiates `ESPBridge`, `PerspectiveWarper`, `GreenDotDetector`, and `NavigationMaster`.
- Executes continuous frame loop with clean exception handling (`KeyboardInterrupt`, serial teardown, `cv2.destroyAllWindows()`).

---

## 5. Strict Formatting, Coding Standards & Testing Guidelines

1. **Header Guards & Clean C++ Inclusions**: Every C++ header file MUST contain robust `#ifndef FILE_NAME_H_` guards. Include only necessary standard libraries and avoid circular inclusions.
2. **Modular Encapsulation**: Maintain strict separation of concerns. Do not mix vision code with serial communication logic or hardware pin definitions across files.
3. **Non-Blocking Core Loops**: NEVER call `delay()` or blocking `sleep()` calls inside high-frequency FreeRTOS tasks or main Python execution loops. Use FreeRTOS `vTaskDelayUntil()` for deterministic periodic tasks and non-blocking timers (`millis()`, `time.time()`).
4. **Thread Safety & Data Integrity**: Protect all shared multi-threaded resources on ESP32 using mutexes (`g_imu_mutex`) or thread-safe queues (`g_command_queue`). Protect PySerial port access in Python using `threading.Lock()`.
5. **CRC Integrity & Hardware Safety Watchdog**: Verify CRC-16-CCITT on EVERY binary serial frame. Enforce the 500ms safety timeout on the ESP32-S3 to cut motor power ($PWM=0$) if communication with the Pi 4B stalls.
6. **Error Logging & Exception Handling**: Implement descriptive logging in Python (`logging` module) and clean debug outputs over Serial on ESP32. Catch serial disconnections gracefully.

---

## 6. Execution Step-by-Step Instructions for Claude Code

Execute the project implementation sequentially across the following distinct phases:

### Phase 1: ESP32-S3 Firmware Infrastructure Construction
1. Create target directory `v2_esp32_firmware/`.
2. Generate `Config.h` containing all pin mapping macros, frequency constants, and system structures.
3. Generate `IMU_Task.h` implementing MPU6050 initialization, calibration, and Core 0 FreeRTOS polling loop with thread-safe mutex protection.
4. Generate `PID_Control.h` implementing 10-sensor IR array sampling, weighted center of gravity position math, discrete PID control, and loss-of-line edge handling.
5. Generate `MotorDriver.h` implementing L298N LEDC hardware PWM setup and directional H-Bridge control routines.
6. Generate `SerialComms.h` implementing binary frame creation, CRC-16 calculation, stream byte parsing, and telemetry dispatching.
7. Generate `DisplayUI.h` implementing SSD1306 OLED telemetry renderer routines.
8. Generate `v2_esp32_firmware.ino` instantiating FreeRTOS tasks pinned to Core 0 and Core 1, task synchronization queues, and main control loop logic.

### Phase 2: Raspberry Pi 4B Python Core Construction
1. Create target directory `v2_pi_core/` and subdirectories `comms/`, `vision/`, `navigation/`.
2. Generate `config.py` with system constants, HSV threshold vectors, homography matrices, and serial parameters. Add `__init__.py` files in package subdirectories.
3. Generate `comms/esp_bridge.py` implementing thread-safe PySerial binary frame packing, CRC16 calculation, and background reading threads.
4. Generate `vision/camera_warp.py` implementing OpenCV 20° tilt homography matrix transformation.
5. Generate `vision/green_dot.py` implementing HSV thresholding, contour area filtering, centroid extraction, and spatial decision matrix logic.
6. Generate `navigation/state_machine.py` implementing master multi-state FSM transitions and action dispatchers.
7. Generate `main.py` tying together camera feed capture, vision processing, FSM updates, and clean program shutdown hooks.

### Phase 3: System Verification & Validation Checklist
- Confirm all target C++ and Python files exist in `v2_esp32_firmware/` and `v2_pi_core/`.
- Verify pin mappings match the hardware blueprint exactly.
- Verify binary packet structures and CRC polynomials are identical between C++ and Python modules.
- Confirm non-blocking operation across all threads and core tasks.
