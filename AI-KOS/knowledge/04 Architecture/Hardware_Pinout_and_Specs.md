# Hardware Pinout & System Specifications

## 1. System Overview
The DPSI-LFR V2 is a high-performance differential drive robot engineered for dual-brain autonomous operation within the AI-KOS ecosystem. Hard real-time sensor processing and motor actuation are decoupled into an **ESP32-S3** microcontroller running FreeRTOS, while high-level computer vision, spatial reasoning, and master state navigation are executed on a **Raspberry Pi 4B** single-board computer running Python 3 and OpenCV.

---

## 2. ESP32-S3 Complete Pin Assignment Table

The ESP32-S3 provides 45 programmable GPIO pins. To maintain maximum signal integrity and prevent boot strapping conflicts (such as GPIO0, GPIO3, GPIO45, GPIO46), pins have been allocated based on peripheral requirements, hardware PWM timers, and dedicated hardware communication buses.

| Peripheral / Subsystem | Function / Signal | ESP32-S3 Pin | Signal Type | Notes / Electrical Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **IR Array (TCRT5000)** | Sensor 1 (Far Left) | `GPIO1` | Digital Input | Pulled LOW on reflection (black line = HIGH) |
| **IR Array (TCRT5000)** | Sensor 2 | `GPIO2` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 3 | `GPIO4` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 4 | `GPIO5` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 5 (Center Left)| `GPIO6` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 6 (Center Right)| `GPIO7` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 7 | `GPIO15` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 8 | `GPIO16` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 9 | `GPIO17` | Digital Input | Pulled LOW on reflection |
| **IR Array (TCRT5000)** | Sensor 10 (Far Right)| `GPIO18` | Digital Input | Pulled LOW on reflection |
| **L298N Motor Driver** | ENA (Left Speed PWM) | `GPIO11` | LEDC PWM Out | 20 kHz PWM, 8-bit resolution |
| **L298N Motor Driver** | IN1 (Left Dir A) | `GPIO12` | Digital Out | Direction logic (HIGH/LOW) |
| **L298N Motor Driver** | IN2 (Left Dir B) | `GPIO13` | Digital Out | Direction logic (LOW/HIGH) |
| **L298N Motor Driver** | IN3 (Right Dir A) | `GPIO14` | Digital Out | Direction logic (HIGH/LOW) |
| **L298N Motor Driver** | IN4 (Right Dir B) | `GPIO21` | Digital Out | Direction logic (LOW/HIGH) |
| **L298N Motor Driver** | ENB (Right Speed PWM)| `GPIO47` | LEDC PWM Out | 20 kHz PWM, 8-bit resolution |
| **I2C Bus (Shared)** | SDA (Serial Data) | `GPIO38` | I2C Bidirectional| Shared by SSD1306 (0x3C) & MPU6050 (0x68) |
| **I2C Bus (Shared)** | SCL (Serial Clock) | `GPIO39` | I2C Clock Out | 400 kHz Fast-Mode I2C Bus |
| **Serial Communication** | UART TX (`TXD0`) | `GPIO43` | UART Output | Connected to Pi 4B (`/dev/ttyUSB0`) @ 115200 baud |
| **Serial Communication** | UART RX (`RXD0`) | `GPIO44` | UART Input | Connected to Pi 4B (`/dev/ttyUSB0`) @ 115200 baud |

*Note: All IR sensor modules feature onboard trimpots for comparator threshold calibration. The ESP32-S3 internal pull-ups are enabled in software for GPIO inputs.*

---

## 3. Power Distribution System & Architecture

The DPSI-LFR V2 utilizes a dual-rail power isolation architecture to separate high-current inductive motor noise from sensitive logic circuitry (Pi 4B, ESP32-S3, IMU, IR sensors).

### Power Architecture Diagram

```
                       +-------------------------+
                       |  12V Battery Pack       |
                       |  (LiPo 3S 11.1V - 12.6V)|
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            | 12V High-Current Rail                         | 12V High-Current Rail
            v                                               v
  +-------------------+                           +-------------------+
  | LM2596 DC-DC Buck |                           | L298N H-Bridge    |
  | Step-Down Module  |                           | Motor Driver      |
  | (Tuned to 5.10V)  |                           +---------+---------+
  +---------+---------+                                     |
            |                                               | 12V PWM Motor Power
            | 5.1V / 3A Regulated Logic Rail                v
            +-----------------------+-------------+   +-------------------+
            |                       |             |   | 2x 12V 600RPM     |
            v                       v             |   | DC Motors         |
    +---------------+       +---------------+     |   +-------------------+
    | Raspberry Pi  |       | ESP32-S3      |     |
    | 4B (5V GPIO)  |       | VIN (5V Pin)  |     |
    +---------------+       +-------+-------+     |
                                    | 3.3V Rail   | 5V Logic Rail
                                    v             v
                             +--------------+  +------------------+
                             | MPU6050 IMU  |  | 10x TCRT5000     |
                             | 0.96" OLED   |  | IR Sensor Array  |
                             +--------------+  +------------------+
```

### Power System Notes & Rules
1. **Common Ground Topology**: A central star-grounding point is established at the L298N power terminal block. The 12V Battery ground, LM2596 input/output ground, ESP32 GND, and Raspberry Pi 4B GND MUST share a zero-impedance common ground reference.
2. **Inductive Noise Filtering**: An electrolytic capacitor ($470\mu\text{F}, 25\text{V}$) and a ceramic decoupling capacitor ($0.1\mu\text{F}$) are placed in parallel across the 12V power supply inputs of the L298N driver to suppress back-EMF voltage spikes generated during motor PWM switching.
3. **Regulator Calibration**: The LM2596 DC-DC buck converter output MUST be measured with a multimeter and tuned to precisely $5.10\text{V} \pm 0.05\text{V}$ under nominal load before connecting to the Raspberry Pi 4B and ESP32-S3 VIN pins to satisfy Pi 4B power supply voltage tolerances.

---

## 4. Chassis Physical Dimensions & Kinematics Model

### 4.1 Physical Specification Summary
- **Drive Configuration**: Differential Drive (2 powered wheels, 1 passive rear omni/caster wheel).
- **Track Width ($W$)**: $140\text{ mm} = 0.140\text{ m}$ (Distance between wheel centerlines).
- **Wheel Diameter ($D_w$)**: $65\text{ mm} = 0.065\text{ m}$ (Wheel radius $R = 0.0325\text{ m}$).
- **Wheelbase ($L_{caster}$)**: $180\text{ mm} = 0.180\text{ m}$ (Distance from main drive axle to rear caster pivot axis).
- **Actuators**: 2x 12V DC Gear Motors, 600 RPM maximum unloaded speed.
- **Max Linear Speed ($v_{max}$)**: $\omega_{max} = 600\text{ RPM} = 10\text{ rev/sec} = 20\pi\text{ rad/s}$.
  $$v_{max} = \omega_{max} \times R = (20\pi\text{ rad/s}) \times 0.0325\text{ m} \approx 2.042\text{ m/s}$$

---

### 4.2 Differential Drive Kinematic Equations

The robot state in the global 2D plane is defined as $q = [x, y, \theta]^T$, where $(x, y)$ represents the center point of the drive axle, and $\theta$ is the heading orientation angle relative to the X-axis.

```
                  ^ Y_robot
                  |
             +----+----+
             |  L-Wheel|  (v_L)
             +----+----+
                  |
                  |     Track Width W = 140mm
                  +-------------> X_robot
                  |
             +----+----+
             |  R-Wheel|  (v_R)
             +----+----+
                  |
           [Axle Center (x,y)]
                  |
                  | Wheelbase L_caster = 180mm
                  |
                  v  [Rear Caster Wheel]
```

#### Forward Kinematics
Given the linear velocities of the right wheel ($v_R$) and left wheel ($v_L$), the robot's net forward linear velocity ($v$) and angular rotational velocity ($\omega$) about the axle center are:

$$v = \frac{v_R + v_L}{2}$$

$$\omega = \frac{v_R - v_L}{W}$$

Where:
- $v_R = R \cdot \omega_R$ (Right wheel linear speed)
- $v_L = R \cdot \omega_L$ (Left wheel linear speed)
- $W = 0.140\text{ m}$

In matrix notation, the kinematic transformation from wheel rotational speeds $[\omega_L, \omega_R]^T$ to robot body velocities $[v, \omega]^T$ is expressed as:

$$\begin{bmatrix} v \\ \omega \end{bmatrix} = \begin{bmatrix} \frac{R}{2} & \frac{R}{2} \\ -\frac{R}{W} & \frac{R}{W} \end{bmatrix} \begin{bmatrix} \omega_L \\ \omega_R \end{bmatrix}$$

#### Inverse Kinematics
Given target robot body velocities $(v, \omega)$ issued by high-level path planning algorithms or PID controllers, the required individual wheel linear velocities ($v_L, v_R$) are calculated as:

$$v_L = v - \frac{\omega \cdot W}{2}$$

$$v_R = v + \frac{\omega \cdot W}{2}$$

#### Instantaneous Center of Rotation (ICR)
When $\omega \neq 0$, the robot rotates in a circular arc around an Instantaneous Center of Rotation (ICR). The distance $R_{ICR}$ from the axle midpoint to the ICR is:

$$R_{ICR} = \frac{v}{\omega} = \frac{W}{2} \left( \frac{v_R + v_L}{v_R - v_L} \right)$$

- If $v_L = v_R$, $R_{ICR} \to \infty$ (Pure translation straight forward).
- If $v_L = -v_R$, $v = 0$ and $R_{ICR} = 0$ (Pure zero-radius pivot turn about axle midpoint).
