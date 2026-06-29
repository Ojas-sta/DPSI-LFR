# Current Task: V2 Architecture & Technical Blueprints Synthesis

## Objective
Provide an up-to-date, comprehensive synthesis of the Technical Blueprints, exact hardware pinouts, FreeRTOS dual-core task design, computer vision algorithms, communication protocol, and complete software component contracts for the DPSI-LFR V2 Differential Drive Robot.

---

## 1. Hardware & System Architecture (LOCKED IN)

### Core Processors & Communication Link
- **Microcontroller (Hard Real-Time)**: ESP32-S3 running C++ with FreeRTOS. Handled subsystems: 10x IR array digital sampling, 100Hz PID line-following, MPU6050 continuous gyro integration on Core 0, L298N H-Bridge PWM motor drive, 0.96" SSD1306 OLED telemetry display.
- **Primary Brain (High-Level Intelligence)**: Raspberry Pi 4B running Python 3 and OpenCV. Handled subsystems: Camera frame acquisition, 20-degree tilt inverse perspective transformation, HSV green dot intersection analysis, master state machine navigation.
- **Communication Bridge**: USB Serial (`/dev/ttyUSB0` on Pi 4B $\leftrightarrow$ UART0 `GPIO43/44` on ESP32-S3) operating at 115,200 baud with custom binary packet framing and CRC-16-CCITT integrity validation.

### Power & Chassis Geometry
- **Power Rail**: 12V Battery Pack supplying high-current motor power directly to L298N VMS input. LM2596 DC-DC Buck Converter tuned to 5.10V supplying logic rails to Raspberry Pi 4B and ESP32-S3 VIN. Single common star ground topology.
- **Motors & Actuators**: 2x 12V 600RPM DC motors driven by L298N H-Bridge driver.
- **Physical Geometry**: Track width $W = 140\text{ mm}$, Drive axle to rear passive caster wheel $L_{caster} = 180\text{ mm}$, Wheel diameter $D_w = 65\text{ mm}$.

---

## 2. Pin Assignment Quick Reference Matrix (ESP32-S3)

| Function | ESP32-S3 Pin | Peripheral / Description |
| :--- | :--- | :--- |
| **IR Array (S1 to S10)** | `GPIO1, 2, 4, 5, 6, 7, 15, 16, 17, 18` | 10x TCRT5000 digital array inputs |
| **L298N Motor Driver** | `GPIO11` (ENA), `GPIO12` (IN1), `GPIO13` (IN2)<br>`GPIO14` (IN3), `GPIO21` (IN4), `GPIO47` (ENB) | Dual-channel PWM + Direction logic |
| **I2C Bus (Shared)** | `GPIO38` (SDA), `GPIO39` (SCL) | SSD1306 OLED (0x3C) & MPU6050 IMU (0x68) |
| **Serial Link** | `GPIO43` (TXD0), `GPIO44` (RXD0) | High-speed UART link to Pi 4B |

---

## 3. Firmware Dual-Core Task Allocation (FreeRTOS)

- **Core 0 Pinned (`Task_IMU_Polling`)**: Priority 5 (Highest), 200 Hz execution frequency. Continuous MPU6050 Z-axis gyro sampling and trapezoidal integration for drift-compensated heading tracking (`g_current_yaw`).
- **Core 1 Main (`Task_LineFollow_PID`)**: Priority 4, 100 Hz execution frequency. Reads 10 IR digital inputs, computes weighted center-of-gravity position error ($e(t) \in [-9.0, +9.0]$), evaluates discrete PID output ($u(t)$), drives L298N PWM. Also executes closed-loop 90-degree pivot turns using Core 0 IMU feedback.
- **Core 1 Serial Parser (`Task_Serial_Parser`)**: Priority 3, event-driven. Decodes binary stream packets, verifies CRC-16, dispatches commands via `g_command_queue`.
- **Core 1 UI (`Task_OLED_Display`)**: Priority 1, 10 Hz execution frequency. Renders real-time telemetry, IR bitmask, integrated yaw, and motor PWM metrics on the SSD1306 OLED screen.

---

## 4. Vision Pipeline & Master State Machine (Raspberry Pi 4B)

### OpenCV Pipeline
1. **Frame Capture**: $640 \times 480$ resolution @ 30 FPS.
2. **Perspective Warp**: Applies $3 \times 3$ Homography matrix transformation matrix ($M$) to rectify 20-degree downward tilt into a $400 \times 400$ metric top-down view.
3. **HSV Color Thresholding**: Converts frame to HSV and masks Green Dots (`Lower: [35, 80, 80]`, `Upper: [85, 255, 255]`).
4. **Contour Analysis**: Filters contours by area ($300 \le A \le 5000\text{ px}^2$) and analyzes spatial centroid offset relative to the main line contour (Left = Left Turn, Right = Right Turn, Both = U-Turn).

### Master Navigation FSM States
- `STATE_LINE_FOLLOWING`: Autonomous high-speed execution handled by ESP32 while Pi monitors visual markers.
- `STATE_INTERSECTION_DECISION`: Overrides line following to issue verified IMU turn commands (`EXECUTE_TURN_90`).
- `STATE_OBSTACLE_AVOIDANCE`: Manages deterministic orbit maneuvers around track obstructions.
- `STATE_RESCUE_ZONE_NAVIGATION`: Navigates rescue arena, locates elements, and identifies exit markers.

---

## 5. Architectural File Layout & Component Contracts

Detailed technical documentation and component contracts have been fully authored across the following blueprint markdown files in `AI-KOS/`:

1. `AI-KOS/knowledge/04 Architecture/Hardware_Pinout_and_Specs.md`: Pinouts, power distribution, and differential kinematics equations.
2. `AI-KOS/knowledge/04 Architecture/ESP32_FreeRTOS_Architecture.md`: FreeRTOS dual-core allocation, 10-sensor weighted PID logic, IMU pivot turn control, OLED UI map.
3. `AI-KOS/knowledge/04 Architecture/RaspberryPi_Vision_and_Navigation.md`: Homography formulas, OpenCV pipeline, green dot logic, master FSM.
4. `AI-KOS/knowledge/04 Architecture/Serial_Communication_Protocol.md`: Packet binary frame, opcodes, CRC-16, handshake, watchdog recovery.
5. `AI-KOS/knowledge/06 Development/File_Structure_and_Component_Design.md`: C++ firmware and Python application file layout, class definitions, function signatures, and component contracts.
