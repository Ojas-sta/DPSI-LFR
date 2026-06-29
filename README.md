<div align="center">
  <h1>🤖 DPSI-LFR: V2 Differential Drive Architecture</h1>
  <p><strong>A Dual-Brain Autonomous Line Following Robot built with Raspberry Pi 4B & ESP32-S3</strong></p>
</div>

---

## ⚡ TL;DR
The DPSI-LFR V2 is a highly robust, dual-processor autonomous robot. It splits responsibilities across two discrete brains: 
1. An **ESP32-S3** handles ultra-fast, hard real-time operations (PID line following at 100Hz, IMU gyro integration at 200Hz, and motor PWM control) using a multi-threaded FreeRTOS environment.
2. A **Raspberry Pi 4B** handles high-level intelligence (OpenCV perspective warping, HSV green dot detection, and master state-machine navigation).

They communicate via a robust USB Serial link (`/dev/ttyUSB0`) utilizing a custom binary packet structure with CRC-16 integrity validation.

---

## 🧠 Dual-Brain Architecture

### 1. The High-Level Brain: Raspberry Pi 4B (Python 3 & OpenCV)
The Raspberry Pi acts as the master commander. It does not worry about keeping the robot on the line; instead, it looks ahead for intersections and obstacles.
- **Vision Pipeline**: Processes a 640x480 @ 30FPS camera feed. It applies a mathematical Homography matrix (perspective warp) to correct a 20-degree downward camera tilt into a top-down metric view.
- **Intersection Analysis**: Uses HSV color thresholding to detect Green Dots indicating left turns, right turns, or U-turns.
- **Master FSM (Finite State Machine)**: Controls the overarching state of the robot (e.g., `STATE_LINE_FOLLOWING`, `STATE_INTERSECTION_DECISION`) and issues macro-commands down to the ESP32.

### 2. The Real-Time Brain: ESP32-S3 (C++ & FreeRTOS)
The ESP32-S3 handles the physical world. It guarantees deterministic execution times for motor control, preventing the robot from oscillating at high speeds.
- **Sensors**: Reads a 10x TCRT5000 IR sensor array (mounted as a single wide line) and an MPU6050 IMU over I2C.
- **Actuators**: Drives an L298N dual H-Bridge connected to 2x 12V 600RPM motors.
- **Debugging UI**: Updates a 0.96" I2C OLED display with real-time telemetry (no physical push buttons are used).

---

## 🧵 FreeRTOS Task Allocation (ESP32-S3)
To ensure the IMU integration never drifts and the PID loop never stutters, the ESP32 utilizes its dual-core architecture via FreeRTOS:

* **Core 0: `Task_IMU_Polling` (Priority 5, 200Hz)**
  * *Purpose*: The most critical task. Continuously polls the MPU6050 Z-axis gyro and performs trapezoidal integration to maintain a drift-compensated, absolute heading (`g_current_yaw`).
* **Core 1: `Task_LineFollow_PID` (Priority 4, 100Hz)**
  * *Purpose*: Reads the 10 IR digital inputs, computes a weighted center-of-gravity position error, evaluates the discrete PID output, and drives the L298N PWM. Also handles closed-loop 90-degree pivot turns using IMU feedback.
* **Core 1: `Task_Serial_Parser` (Priority 3, Event-Driven)**
  * *Purpose*: Listens to the UART bus, decodes incoming binary packets from the Pi, verifies the CRC-16 checksum, and dispatches commands.
* **Core 1: `Task_OLED_Display` (Priority 1, 10Hz)**
  * *Purpose*: Renders real-time telemetry (IR bitmask, integrated yaw, motor PWM) to the SSD1306 OLED screen for physical debugging.

---

## 📡 Communication Protocol
The Pi and ESP32 are connected via a physical USB cable acting as a UART Serial bridge (`/dev/ttyUSB0`) running at 115,200 baud. 
- **Packet Structure**: Every transmission uses a custom 8-byte binary frame: `[START_BYTE] [OPCODE] [PAYLOAD_1..4] [CRC_H] [CRC_L]`.
- **Integrity**: A CRC-16-CCITT checksum ensures that electrical noise from the DC motors does not corrupt serial commands.
- **Watchdog/Heartbeat**: The Pi continuously sends `HEARTBEAT_PING` packets. If the ESP32 does not receive a ping within a defined timeout (e.g., the Pi crashes or the USB unplugs), the ESP32 triggers an emergency motor halt.

---

## 📚 AI-KOS Knowledge Base (Markdown Blueprints)
This repository was architected using the **AI-KOS (AI Knowledge Operating System)** framework. The extensive architectural blueprints are located in the `AI-KOS/` directory:

### Core Context
* `CurrentTask.md`: The living, high-level blueprint outlining the exact hardware specifications, geometry (140mm track width, 180mm caster distance), and division of labor.
* `Claude_Code_Prompt.md`: The massive 22KB synthesized prompt that was used to generate the Python and C++ codebases.

### Architecture Deep Dives (`AI-KOS/knowledge/04 Architecture/`)
* `Hardware_Pinout_and_Specs.md`: Documents every GPIO pin mapping, power distribution logic (12V battery vs 5.1V logic rails), and differential kinematics math.
* `ESP32_FreeRTOS_Architecture.md`: Deep dive into the RTOS scheduling, the 10-sensor weighted PID algorithm, and the IMU pivot turn control theory.
* `RaspberryPi_Vision_and_Navigation.md`: Documents the mathematical Homography matrix formulations, OpenCV processing pipelines, and FSM transition tables.
* `Serial_Communication_Protocol.md`: Defines the exact binary packet structure, supported opcodes (e.g., `<TURN_90_LEFT>`, `<SET_SPEEDS>`), and the CRC-16 generation algorithm.
* `diagram1.md`: A Mermaid graph visualizing the hardware data flow and subsystem connections.

### Development Contracts (`AI-KOS/knowledge/06 Development/`)
* `File_Structure_and_Component_Design.md`: The structural contract binding the C++ (`v2_esp32_firmware/`) and Python (`v2_pi_core/`) directories together, establishing class boundaries and function signatures.

---

*Note: For an interactive map of these documents, refer to the `DPSI_LFR_Obsidian_Hub.md` file in the root directory if you are using Obsidian.*
