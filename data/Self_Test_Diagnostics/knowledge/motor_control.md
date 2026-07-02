# Technical Blueprint: L298N Motor Control & Safety Watchdog Architecture

## 1. Subsystem Overview

The motor control subsystem translates high-level directional commands and velocity targets from either the automated PID line-following algorithm or manual WebSocket web dashboard inputs into physical wheel locomotion. The actuators are driven by an H-Bridge L298N motor driver module interfaced directly with the ESP32-S3 microcontroller. 

Precision speed modulation is performed using the ESP32-S3 hardware LEDC (PWM) peripheral, while directional switching is governed by digital GPIO logic states. Safety is enforced at hardware and software abstraction levels through fail-safe truth tables and a non-blocking watchdog timer.

---

## 2. Hardware Pin Mappings & LEDC PWM Configuration

### 2.1 Hardware Interfacing
The L298N dual H-bridge controller interface requires 6 control lines from the ESP32-S3 GPIO matrix:

| Functional Signal | Microcontroller Pin | Signal Type | Target Subsystem |
| :--- | :---: | :---: | :--- |
| **`PIN_MOTOR_ENA`** | GPIO 11 | Hardware LEDC PWM | Left Motor Enable / Speed Control |
| **`PIN_MOTOR_IN1`** | GPIO 12 | Digital Output | Left Motor Direction Input A |
| **`PIN_MOTOR_IN2`** | GPIO 13 | Digital Output | Left Motor Direction Input B |
| **`PIN_MOTOR_IN3`** | GPIO 14 | Digital Output | Right Motor Direction Input A |
| **`PIN_MOTOR_IN4`** | GPIO 21 | Digital Output | Right Motor Direction Input B |
| **`PIN_MOTOR_ENB`** | GPIO 47 | Hardware LEDC PWM | Right Motor Enable / Speed Control |

### 2.2 ESP32-S3 LEDC Hardware Peripheral Setup
The ESP32-S3 LEDC (LED Control) peripheral provides high-precision pulse-width modulation without requiring CPU intervention once initialized.

```
+-----------------------------------------------------------------------------------+
|                            LEDC HARDWARE PERIPHERAL                               |
|                                                                                   |
|  Timer Allocation: LEDC_TIMER_0 (Shared, 20000 Hz, 8-Bit)                         |
|  +-----------------------------------------------------------------------------+  |
|  | PWM Frequency  : 20,000 Hz (20 kHz, ultrasonic to eliminate motor whine)   |  |
|  | Resolution     : 8-Bit Duty Cycle (Duty values range strictly from 0 to 255)|  |
|  +-----------------------------------------------------------------------------+  |
|                                     |                                             |
|                     +---------------+---------------+                             |
|                     |                               |                             |
|                     v                               v                             |
|       LEDC Channel 0 (`LEDC_CHANNEL_LEFT`)   LEDC Channel 1 (`LEDC_CHANNEL_RIGHT`)|
|       Mapped to GPIO 11 (Left Motor)        Mapped to GPIO 47 (Right Motor)      |
+-----------------------------------------------------------------------------------+
```

#### Detailed LEDC Parameters
- **PWM Frequency**: `20000 Hz` (20 kHz). This ultrasonic frequency prevents audible motor inductance hum and minimizes acoustic noise during operation.
- **PWM Resolution**: `8 bits` (`PWM_RESOLUTION_BITS`). Yields an integer duty cycle resolution of $2^8 = 256$ distinct levels ($0$ to $255$).
- **Channel Allocation**:
  - `LEDC_CHANNEL_LEFT = 0` bound to GPIO 11.
  - `LEDC_CHANNEL_RIGHT = 1` bound to GPIO 47.

---

## 3. Directional Control State Machine & Truth Table

### 3.1 Digital State Matrix
Motor rotation direction and electrical braking are controlled by setting digital high (`HIGH` / `1`) or low (`LOW` / `0`) logic levels on inputs `IN1` through `IN4`.

| Motion State | `IN1` (GPIO 12) | `IN2` (GPIO 13) | `IN3` (GPIO 14) | `IN4` (GPIO 21) | Left PWM | Right PWM | Motion Description |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`HARD_STOP`** | `LOW` | `LOW` | `LOW` | `LOW` | `0` | `0` | Coast / Complete Disengage |
| **`BRAKE`** | `HIGH` | `HIGH` | `HIGH` | `HIGH` | `255` | `255` | Active Electrical Brake |
| **`FORWARD`** | `HIGH` | `LOW` | `HIGH` | `LOW` | $V_{left}$ | $V_{right}$ | Both wheels forward |
| **`REVERSE`** | `LOW` | `HIGH` | `LOW` | `HIGH` | $V_{left}$ | $V_{right}$ | Both wheels in reverse |
| **`PIVOT_LEFT`** | `LOW` | `HIGH` | `HIGH` | `LOW` | $V_{left}$ | $V_{right}$ | Counter-rotate (Spin in place left) |
| **`PIVOT_RIGHT`**| `HIGH` | `LOW` | `LOW` | `HIGH` | $V_{left}$ | $V_{right}$ | Counter-rotate (Spin in place right)|
| **`TURN_LEFT`** | `LOW` | `LOW` | `HIGH` | `LOW` | `0` | $V_{right}$ | Left wheel stopped, right forward |
| **`TURN_RIGHT`**| `HIGH` | `LOW` | `LOW` | `LOW` | $V_{left}$ | `0` | Right wheel stopped, left forward |

---

## 4. PWM Speed Regulation Architecture

### 4.1 Speed Boundaries & Calibration
Motor velocity $V$ is expressed as an 8-bit duty cycle integer $V \in [0, 255]$.

- **Minimum Operational Threshold ($V_{min}$)**: Due to internal friction and mechanical inertia, DC motors require a minimum starting voltage. The firmware sets the effective baseline operational speed to `150` (`BASE_SPEED`).
- **Maximum Speed Limit ($V_{max}$)**: Capped at `255` (`PID_OUTPUT_MAX`).
- **Differential Speed Computation**: During line-following operations or manual proportional turning, differential speed offsets generated by PID algorithms are clamped between `0` and `255`:
  $$\text{Duty}_{\text{Left}} = \text{clamp}(\text{Speed}_{\text{Base}} + \Delta V, 0, 255)$$
  $$\text{Duty}_{\text{Right}} = \text{clamp}(\text{Speed}_{\text{Base}} - \Delta V, 0, 255)$$

---

## 5. Motor Safety Watchdog Logic

### 5.1 Fail-Safe Objective
In wireless diagnostic environments, Wi-Fi link dropouts, browser crashes, or packet loss can cause the robot to maintain its last received movement command indefinitely. To eliminate runaway vehicle hazards, a dedicated software watchdog timer monitors incoming WebSocket control payloads.

```
                         WebSocket Control Packet Received
                                       |
                                       v
                        Update `last_packet_time = millis()`
                                       |
                                       v
                 +-------------------------------------------+
                 | FreeRTOS MotorWatchdogTask (Runs every 10ms)|
                 +-------------------------------------------+
                                       |
                   Is `(millis() - last_packet_time) > 500ms`?
                                  /         \
                                 /           \
                              YES             NO
                              /                 \
                             v                   v
                    +-------------------+   +--------------------+
                    | Emergency Stop!   |   | Maintain Normal    |
                    | `HARD_STOP` state |   | Motor Operation    |
                    | Set PWM = 0       |   +--------------------+
                    +-------------------+
```

### 5.2 Technical Watchdog Parameters
- **Timeout Threshold**: `500 ms` (`WATCHDOG_TIMEOUT_MS`).
- **Execution Context**: Evaluated continuously within the `MotorControlTask` or a dedicated FreeRTOS timer service on Core 1 every 10 ms.
- **State Transition**: Upon timeout expiration (`current_time - last_rx_timestamp > WATCHDOG_TIMEOUT_MS`), the watchdog forces an immediate state transition to `HARD_STOP` by driving `IN1`–`IN4` to `LOW` and clearing both LEDC channels (`ledcWrite(0, 0)` and `ledcWrite(1, 0)`).
- **Recovery Protocol**: The motor driver remains locked in `HARD_STOP` until a newly validated WebSocket control packet is decoded and verified.
