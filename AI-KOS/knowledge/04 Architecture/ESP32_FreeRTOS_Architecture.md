# ESP32-S3 FreeRTOS Architecture & Control Systems

## 1. Executive Overview
The ESP32-S3 microcontroller handles hard real-time execution in the DPSI-LFR V2 robotics architecture. Operating under **FreeRTOS**, the system leverages symmetric multiprocessing (SMP) across two Xtensa 32-bit LX7 cores running at 240MHz. Real-time tasks are strictly partitioned between dedicated IMU sensor integration on Core 0 and high-frequency line-following control loops, motor drivers, display updates, and serial telemetry parsing on Core 1.

---

## 2. Dual-Core Task Allocation & Synchronization Architecture

### 2.1 Task Allocation Matrix

| Task Name | Pinned Core | Priority | Stack Size | Execution Frequency | Primary Responsibilities |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Task_IMU_Polling` | **Core 0** | 5 (Highest) | 4096 bytes | 200 Hz (5 ms period) | MPU6050 I2C sampling, low-pass filtering, high-frequency Z-axis gyro integration for continuous drift-compensated yaw tracking. |
| `Task_LineFollow_PID` | **Core 1** | 4 (High) | 8192 bytes | 100 Hz (10 ms period)| 10x TCRT5000 digital array sampling, line position error calculation, PID loop computation, L298N PWM generation, state machine transitions. |
| `Task_Serial_Parser` | **Core 1** | 3 (Medium) | 4096 bytes | Event-Driven / RX ISR | Ring buffer decoding of USB Serial packets (`/dev/ttyUSB0` @ 115200 baud), CRC validation, command queue dispatching. |
| `Task_OLED_Display` | **Core 1** | 1 (Lowest) | 3072 bytes | 10 Hz (100 ms period)| Local SSD1306 OLED telemetry updates, state visualizer, IR bitmask rendering, diagnostic readout. |

---

### 2.2 Inter-Task Communication & Synchronization Diagram

```
[Core 0]                                             [Core 1]
+--------------------+                               +--------------------+
|  Task_IMU_Polling  |                               | Task_LineFollow_PID|
|  (200Hz)           |                               | (100Hz Main Loop)  |
+---------+----------+                               +---------+----------+
          |                                                    |
          | Write Yaw Angle                                    | Read Yaw Angle
          v                                                    v
+-------------------------------------------------------------------------+
| g_imu_mutex (FreeRTOS SemaphoreMutex) - Protects float g_current_yaw    |
+-------------------------------------------------------------------------+
                                                               ^
                                                               | Dispatch Turn Command
                                                               |
+-------------------------------+                     +--------+-----------+
| USB Serial RX Interrupt (ISR) | --(Raw Bytes)--->   | Task_Serial_Parser |
+-------------------------------+                     +--------+-----------+
                                                               |
                                                               | Enqueue Motor Commands
                                                               v
+-------------------------------------------------------------------------+
| g_command_queue (FreeRTOS Queue, depth=10, struct CommandPacket)       |
+-------------------------------------------------------------------------+
```

### 2.3 Synchronization Primitives
1. **`g_imu_mutex` (Mutex Semaphore)**: Guarantees thread-safe access to the shared global floating-point variable `g_current_yaw`. `Task_IMU_Polling` holds the mutex for $< 5\mu\text{s}$ to update integrated heading. `Task_LineFollow_PID` locks this mutex during 90-degree IMU turn execution.
2. **`g_command_queue` (FreeRTOS Queue)**: A thread-safe FIFO queue (`depth = 10`, `item_size = sizeof(CommandPacket)`) used by `Task_Serial_Parser` to send override motor commands, setpoints, or turn triggers (`EXECUTE_TURN_90`) directly to `Task_LineFollow_PID`.

---

## 3. 10-Sensor Weighted PID Line-Following Algorithm Specification

The robot front line sensor array consists of 10 TCRT5000 digital IR reflectometers placed side-by-side spanning a total width of 180mm.

```
Sensor Layout (Front View looking down):
[ S1 ] [ S2 ] [ S3 ] [ S4 ] [ S5 ] [ S6 ] [ S7 ] [ S8 ] [ S9 ] [ S10 ]
 -9     -7     -5     -3     -1     +1     +3     +5     +7     +9   <-- Assigned Weights
```

### 3.1 Weighted Sensor Position & Error Calculation
Each sensor $S_i \in \{0, 1\}$ returns `1` when detecting the black line and `0` when detecting white background. Fixed spatial weights $W_i$ are assigned symmetrically from center:

$$W = [-9, -7, -5, -3, -1, +1, +3, +5, +7, +9]$$

The calculated center-of-gravity line position $P_{line}$ is computed as:

$$P_{line} = \frac{\sum_{i=1}^{10} (S_i \cdot W_i)}{\sum_{i=1}^{10} S_i}$$

#### Edge Cases & Loss of Line Protocol:
- **Line Centered**: If $S_5=1$ and $S_6=1$, $P_{line} = \frac{(-1 \cdot 1) + (+1 \cdot 1)}{2} = 0.0$.
- **Active Line Detected ($\sum S_i > 0$)**: Error $e(t) = P_{target} - P_{line} = 0 - P_{line} = -P_{line}$.
- **Line Lost Condition ($\sum S_i = 0$)**: If all sensors read white background (e.g., crossing a gap or sharp turn), $e(t)$ retains the sign of the last valid non-zero error ($e_{last}$) with an inflated magnitude coefficient ($\pm 12.0$) to force aggressive recovery turning toward the direction where the line was last seen.

---

### 3.2 Discrete PID Equations & Implementation Details

The PID output $u(t)$ modifies differential motor speeds around a configurable base PWM speed ($V_{base}$).

$$P(t) = K_p \cdot e(t)$$

$$I(t) = I(t-1) + K_i \cdot e(t) \cdot \Delta t$$

$$D(t) = K_d \cdot \frac{e(t) - e(t-1)}{\Delta t}$$

$$u(t) = P(t) + I(t) + D(t)$$

#### Anti-Windup & Output Clamping:
To prevent integral windup when wheels saturate:
1. $I(t)$ accumulation is clamped to a maximum limit: $|I(t)| \le I_{max}$ (where $I_{max} = 50.0$).
2. Final control signal $u(t)$ is bounded: $-255 \le u(t) \le 255$.

#### Motor Speed Mixing Logic:
$$PWM_{Left} = \text{Constrain}(V_{base} + u(t), -255, 255)$$

$$PWM_{Right} = \text{Constrain}(V_{base} - u(t), -255, 255)$$

When PWM value is negative, H-bridge direction logic (IN1/IN2 or IN3/IN4) inverts motor polarity to perform active reverse braking/turning on the inside wheel.

---

### 3.3 Empirical Tuning Methodology (Ziegler-Nichols Heuristic)
1. **Initial State**: Set $K_i = 0$, $K_d = 0$. Gradually increase $K_p$ from 0 until the robot follows a straight line but exhibits continuous sustained oscillation around the line (Ultimate Gain $K_u$). Record oscillation period $T_u$.
2. **PID Coefficient Calculation**:
   - $K_p = 0.6 \cdot K_u$
   - $K_i = \frac{1.2 \cdot K_p}{T_u}$
   - $K_d = \frac{3.0 \cdot K_p \cdot T_u}{40}$
3. **Fine Tuning**: Increase $K_d$ to dampen sharp oscillations when entering high-curvature bends. Keep $K_i$ minimal ($< 0.05$) to avoid instability caused by sensor digital discretization lag.

---

## 4. Precision 90-Degree IMU Turn Control Loop

When the Pi 4B detects a Green Dot intersection command (e.g., `EXECUTE_TURN_90` with direction parameter `DIR_LEFT` or `DIR_RIGHT`), `Task_LineFollow_PID` temporarily suspends line following and engages the IMU closed-loop pivot controller on Core 0 / Core 1.

### 4.1 MPU6050 Continuous Yaw Integration (Core 0)
`Task_IMU_Polling` reads the Z-axis gyroscope angular velocity $G_z$ ($\text{deg/sec}$) via I2C at 200 Hz ($\Delta t = 0.005\text{ s}$).
1. **Calibration**: Upon boot, 500 samples are taken while stationary to compute gyroscope bias offset $G_{z\_offset}$.
2. **Integration**:
   $$G_{z\_filtered} = G_z - G_{z\_offset}$$
   $$g\_current\_yaw = g\_current\_yaw + (G_{z\_filtered} \cdot \Delta t)$$

---

### 4.2 Pivot Turn Execution State Machine Logic

```
[Start Turn Signal] ---> Capture Baseline Yaw Y0
                                |
                                v
                    Calculate Target Y_target = Y0 ± 90.0°
                                |
                                v
                   +--------------------------+
                   | Differential Spin Motors |
                   | Left: -150, Right: +150  |
                   +------------+-------------+
                                |
                                v
                     Check Error |Y_target - Y_current| < 15.0°?
                                |
                        +-------+-------+
                        | Yes           | No
                        v               v
            Proportional Slowdown   Continue Spin
            Scale PWM to ±60
                        |
                        v
         Check Threshold |Y_target - Y_current| <= 0.5°?
                        |
                        v
             Active Brake Both Motors (PWM = 0)
                        |
                        v
         Send TURN_COMPLETE Telemetry Packet to Pi 4B
```

#### Pivot Turn Control Parameters:
- **Spin Speed**: Fast phase = PWM $\pm 150$; Slowdown phase ($< 15.0^\circ$ remaining) = PWM scaled proportionally down to minimum threshold $\pm 60$.
- **Target Tolerance**: Deadband of $\pm 0.5^\circ$.
- **Completion Signal**: Upon reaching target tolerance, motors execute reverse pulse braking for $20\text{ms}$, then return `TURN_COMPLETE` packet over Serial to Raspberry Pi 4B.

---

## 5. OLED Local Telemetry UI Layout Specification

The 0.96-inch I2C SSD1306 OLED display ($128 \times 64$ resolution) provides real-time diagnostic telemetry rendered by `Task_OLED_Display` at 10 Hz without blocking control execution.

### Display Buffer Graphical Map ($128 \times 64$ Pixels)

```
+-------------------------------------------------+
| MODE: LINE_FOLLOW      [BATT: 12.1V]  (Row 0-15)|
| IR: 0 0 1 1 1 1 0 0 0 0               (Row 16-31)|
| YAW: +089.4 deg        ERR: +0.50     (Row 32-47)|
| L_PWM: +180  R_PWM: +140 | SYS: OK    (Row 48-63)|
+-------------------------------------------------+
```

### Detailed Row Breakdown:
1. **Row 0-15 (Header Block)**:
   - Font: $6 \times 8$ Monospace.
   - Content: System mode status (`LINE_FOLLOW`, `IMU_TURN`, `EMERGENCY_STOP`, `SEARCHING`) aligned left; battery voltage readout aligned right.
2. **Row 16-31 (Sensor Visualizer Block)**:
   - Graphic: 10 solid/empty rectangles representing the live 10-bit digital state of TCRT5000 IR sensors (`1` = filled box, `0` = empty outline).
3. **Row 32-47 (Kinematics & Telemetry Block)**:
   - Content: Real-time MPU6050 integrated heading (`YAW: ±XXX.X deg`) and current PID error value (`ERR: ±XX.XX`).
4. **Row 48-63 (Actuator Output Block)**:
   - Content: Live PWM duty cycles delivered to L298N H-Bridge (`L_PWM`, `R_PWM`) and hardware system status heartbeat flag.
