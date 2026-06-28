# DPSI-LFR: Autonomous Rescue Line Follower (v2)

## Overview
DPSI-LFR v2 is a completely overhauled, high-performance autonomous line-following robot designed for the **Rescue Robotics Arena** competition. Moving away from the heavy v1 mecanum chassis, v2 utilizes a **smaller, custom 2-layered chassis** with a **differential drive system**.

To achieve both high-speed precision and advanced strategic navigation, the robot uses a dual-brain architecture: a **Raspberry Pi 4B** handles heavy computer vision and AI pathfinding, while an **ESP32-S3** manages real-time, low-latency motor control and sensor polling.

## Core Features (v2 Architecture)
- **Differential Drive System:** 2x 600 RPM high-speed motors with a rear caster for agile, rapid maneuvering.
- **Dual-Brain Processing:** 
  - **Raspberry Pi 4B:** Runs the high-level Python AI stack, OpenCV camera vision (detecting green dots, gaps, and intersections), and hosts the WebSocket telemetry dashboard.
  - **ESP32-S3:** Runs C++ firmware for hard-real-time tasks—polling the 10 IR sensors and executing rapid PID motor control loops.
- **Discrete IR Sensing:** Replaced the sluggish 1-Wire protocol with direct GPIO polling of 10x IR Sensors (two 5-Channel TCRT5000 arrays) for zero-latency line detection.
- **High-Speed Serial Bridge:** The Pi and ESP32-S3 communicate via a rapid UART/USB serial protocol to exchange telemetry and motor commands seamlessly.

---

## Technical Specifications

### Hardware List
- **Primary Brain:** Raspberry Pi 4B (Python / OpenCV)
- **Vision:** Raspberry Pi Camera
- **Real-Time Controller:** ESP32-S3 (Arduino/C++)
- **Chassis:** Custom 2-layered small footprint chassis
- **Motors:** 2x 12V 600 RPM DC Motors
- **Motor Driver:** Dual H-Bridge (e.g., L298N)
- **Sensors:** 10x IR Sensors (2x 5-Channel TCRT5000)

### ESP32-S3 Pinout Configuration
*(Safely avoids all internal flash, USB, and dangerous strapping pins)*

**Motor Driver (L298N)**
| Component | Pin | Function |
| :--- | :--- | :--- |
| **ENA** | GPIO 4 | Left Motor PWM (Speed) |
| **IN1** | GPIO 5 | Left Motor Forward |
| **IN2** | GPIO 6 | Left Motor Reverse |
| **IN3** | GPIO 7 | Right Motor Forward |
| **IN4** | GPIO 15 | Right Motor Reverse |
| **ENB** | GPIO 16 | Right Motor PWM (Speed) |

**Sensor Array 1 (Front - 5x IR)**
| Sensor | Pin |
| :--- | :--- |
| **S1** | GPIO 8 |
| **S2** | GPIO 9 |
| **S3** | GPIO 10 |
| **S4** | GPIO 11 |
| **S5** | GPIO 12 |

**Sensor Array 2 (Left/Secondary - 5x IR)**
| Sensor | Pin |
| :--- | :--- |
| **S1** | GPIO 13 |
| **S2** | GPIO 14 |
| **S3** | GPIO 17 |
| **S4** | GPIO 18 |
| **S5** | GPIO 21 |

---

## Directory Structure
Development has moved entirely to the new `v2` directories. Legacy v1 code has been archived for reference.

```text
DPSI-LFR/
├── v2_pi_core/           # (NEW) Raspberry Pi 4B code (Python, OpenCV, WebSockets)
├── v2_esp32_firmware/    # (NEW) ESP32-S3 code (C++, PID loops, Sensor drivers)
├── docs/                 # Technical documentation and competition rules
├── claude_context.md     # v2 Architecture Migration Guide
├── BreadboardTest/       # (ARCHIVED) v1 testing scripts
├── MecanumWebControl/    # (ARCHIVED) v1 quad-motor control
└── README.md             # Project Overview
```

## Setup & Migration
For complete details on the migration from the v1 Mecanum setup to the new v2 Differential setup, please refer to the [v2 Migration Guide](./claude_context.md).

---
© 2026 DPSI Rescue Robotics Team. All rights reserved.
