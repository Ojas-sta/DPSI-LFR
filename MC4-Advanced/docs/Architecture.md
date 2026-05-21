# MC4.0 Advanced Architecture: Distributed Intelligence

## 1. System Overview
The new architecture evolves the robot from a monolithic controller to a distributed system. This offloads timing-critical sensor reading and low-level motor PID to secondary processors, freeing the **M5 Core 2** for high-level AI, path planning, and UI.

### Hardware Stack:
1.  **Main Controller (M5 Core 2)**:
    *   **Role**: Master AI and Decision Making.
    *   **Communication**: I2C Master (to Motor Module), UART Master (to Sensor Pod).
    *   **Logic**: Runs the perception engine and translates AI vectors into velocity commands.
2.  **Motor Controller (STM32 4-Encoder Motor Module)**:
    *   **Role**: Real-time Motor Control.
    *   **Connection**: Stacks directly via M-Bus (I2C Address `0x24`).
    *   **Capabilities**: 4-channel independent control, Position PID, Speed PID, and Current Monitoring.
3.  **Sensor Processor (ESP32 C3 Super Mini)**:
    *   **Role**: Dedicated "Sensor Pod" controller.
    *   **Connection**: Linked to M5 Core 2 via UART.
    *   **Task**: Continuously polls the 20-sensor (5x4) IR grid via 1-Wire protocol (`WeMultipleLineFollower`). Pre-processes raw data into a serialized bitmask or vector to send to the Core 2.

## 2. Component Analysis

### A. The 4-Encoder Motor Module (STM32)
Based on the `M5Module4EncoderMotor` documentation:
*   **Modes**:
    *   `NORMAL_MODE`: Direct PWM control (8-bit).
    *   `POSITION_MODE`: Move to a specific encoder count using onboard PID.
    *   `SPEED_MODE`: Maintain a constant RPM regardless of load.
*   **Safety**: Built-in current monitoring (`getMotorCurrent()`) and analog voltage sensing for battery protection.

### B. The Line Follower Array (5x4 Grid)
Using the `WeMultipleLineFollower` library:
*   **Protocol**: Custom 1-Wire protocol.
*   **Data Structure**: Each read returns a 5-byte set (one per column) or a single summarized 8-bit/16-bit value.
*   **Distributed Advantage**: By using the **ESP32 C3** as a buffer, the M5 Core 2 no longer has to wait for 1-Wire bit-banging, which can block the CPU for several milliseconds.

## 3. Communication Protocol (UART - Sensor to Core 2)
The ESP32 C3 should transmit data in a lightweight binary format:
- `[START_BYTE][GRID_BYTE_1][GRID_BYTE_2][GRID_BYTE_3][GRID_BYTE_4][GRID_BYTE_5][CHECKSUM]`
- This ensures the Core 2 always has a 20-bit representation of the floor in its buffer ready for the CNN/PCA engine.

## 4. Logical Workflow
1.  **C3 Sensor Pod**: Reads 20 sensors $\rightarrow$ Packs into 5 bytes $\rightarrow$ Sends via UART.
2.  **M5 Core 2**: Receives UART $\rightarrow$ Runs PCA/CNN Engine $\rightarrow$ Calculates Velocity ($V$) and Yaw ($\omega$).
3.  **Core 2**: Converts $V$ and $\omega$ into 4 independent wheel speeds $\rightarrow$ Sends I2C commands to **STM32 Motor Module**.
4.  **STM32 Module**: Executes PID loops to maintain speeds exactly as commanded.
