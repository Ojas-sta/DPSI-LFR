# DPSI-LFR: Autonomous Rescue Line Follower

## Overview
DPSI-LFR is a high-performance, autonomous line-following robot built on the **MC4.0 Industrial Chassis**. Designed for the **Rescue Robotics Arena** competition, the system leverages a **Distributed Triple-Processor Architecture** (M5 Core 2, ESP32 C3, and STM32) and a custom 20-sensor IR grid (5x4) to navigate complex tracks featuring intersections, gaps, ramps, and obstacles.

This project implements a **Trainable CNN-based Grid Classifier** and a **PCA-driven Visual Compass** for precision navigation and victim rescue simulation.

## Core Features
- **Distributed Intelligence:** Triple-processor model offloading timing-critical tasks to dedicated MCUs for zero-latency control.
- **Hybrid Perception Engine:** Combines a Trainable CNN with Topological Analysis (BFS) to interpret 4x5 sensor grids with 99% accuracy.
- **AI Vector Steering:** Uses PCA (Principal Component Analysis) to extract physical heading vectors, enabling **Encoder-less Orientation Control**.
- **Fused Perception (AI + MPU6050):** A dual-loop control system using Visual AI for precision "Catching" and the MPU6050 for high-speed "Blind Pivots."
- **MC4.0 Platform Control:** Quad-motor independent drive system using high-torque encoder motors and Mecanum wheels for omnidirectional maneuverability.
- **20-Sensor Grid Support:** Interfaced via a custom 1-Wire protocol for high-density surface mapping.
- **Web-Based Telemetry:** Live WebSocket dashboard for real-time sensor visualization and manual motor control.
- **Competition Optimized:** Designed specifically for the Rescue Robotics Arena 2026 ruleset.

---

## Technical Specifications

### Hardware List
- **Microcontroller:** ESP32 (30-pin)
- **Motors:** 4x DS12V 200RPM DC Gear Motors
- **Motor Driver:** 2x TB6612FNG Dual Channel Drivers (Parallel Wiring)
- **Power:** 3S LiPo Battery (11.1V Nominal, 12.6V Max)
- **Regulation:** LM2596 Step-Down Buck Converter (5V Logic Rail)
- **Sensors:** Custom 5x4 Grid Line Follower Array (1-Wire Protocol)

### Pinout Configuration
| ESP32 Pin | Peripheral Pin | Function |
| :--- | :--- | :--- |
| D12 | FL - PWMA | Front Left Speed (PWM) |
| D27 | FL - AIN1 | Front Left Direction 1 |
| D14 | FL - AIN2 | Front Left Direction 2 |
| D13 | FL - STBY | Front Left Driver Enable |
| D21 | FR - PWMB | Front Right Speed (PWM) |
| D23 | FR - BIN1 | Front Right Direction 1 |
| D22 | FR - BIN2 | Front Right Direction 2 |
| D15 | FR - STBY | Front Right Driver Enable |
| D32 | RL - PWMA | Rear Left Speed (PWM) |
| D35 | RL - AIN1 | Rear Left Direction 1 |
| D34 | RL - AIN2 | Rear Left Direction 2 |
| D33 | RL - STBY | Rear Left Driver Enable |
| D19 | RR - PWMB | Rear Right Speed (PWM) |
| D18 | RR - BIN1 | Rear Right Direction 1 |
| D5  | RR - BIN2 | Rear Right Direction 2 |
| D4  | RR - STBY | Rear Right Driver Enable |
| D26 | Sensor SIG | 1-Wire Data Line |
| RX0 | Red LED | Indicator (Via 200Ω Resistor) |
| TX0 | Green LED | Indicator (Via 200Ω Resistor) |

---

## Development Log
Detailed records of technical breakthroughs and session updates can be found in the [FEATURE_LOG.md](./FEATURE_LOG.md).

**Latest Major Update (2026-05-20):**
- Implementation of **Distributed Architecture** (M5 Core 2 + ESP32 C3).
- Launch of **Ultra-Low Latency WebSocket Telemetry** interface.
- Integration of **PCA-based AI Vector Steering** for encoder-less control.

---

## Directory Structure
```text
DPSI-LFR/
├── docs/               # Technical documentation and competition rules
├── src/                # Source code for ESP32 and AI models
├── resources/          # Circuit diagrams and design links
├── FEATURE_LOG.md      # Timestamped development and feature log
└── README.md           # Project Overview
```

## Project Links
- [Main Circuit Design](https://app.cirkitdesigner.com/project/f580b8e3-f0ca-49b9-80c8-28521a5a5665)
- [Alternative Prototype](https://app.cirkitdesigner.com/project/3d586156-ec8d-4c36-8379-9c99c1b2dfc7)
- [Final Prototype Design](https://app.cirkitdesigner.com/project/1892f78e-7115-4b1b-a62e-ec4acb310e49)
- [Project Gallery](https://photos.app.goo.gl/16j9BJs6UpAgtNSf6)

---

## Implementation Notes & Risks
- **Current Limits:** Caution must be used when driving 4 motors on a single rail; ensures heavy-duty wiring for VMOT.
- **Reflectivity:** Calibration is required for Sunmica vs. Whiteboard surfaces.
- **Marker Logic:** Distinguishing "Green Dots" from "90-degree turns" is handled via the CNN grid classifier.

---
© 2026 DPSI Rescue Robotics Team. All rights reserved.
