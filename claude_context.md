# DPSI-LFR v2 Migration & Context Guide

## 1. Project Overview & Motivation
We are migrating the **DPSI-LFR (Line Following Robot)** from its v1 architecture to a **completely new v2 architecture**, starting from scratch. 
The v1 architecture was heavy, used 4 mecanum wheels with 4 motors, a complex 5x4 IR grid over a 1-Wire protocol, and a triple-processor setup. 

**v2 Design Philosophy:** Lighter, faster, and smarter. We are transitioning to a smaller, modern chassis with a differential drive system (2 motors + caster), utilizing a powerful Raspberry Pi 4B for high-level vision/control and an ESP32-S3 for real-time motor/sensor operations.

## 2. Hardware Migration Summary

| Component | v1 Architecture | v2 Architecture |
| :--- | :--- | :--- |
| **Chassis** | MC4.0 Industrial Chassis | Modern, smaller custom 2-layered/level chassis |
| **Drive System** | Quad-motor Mecanum (Omnidirectional) | Differential Drive (2x 600RPM Motors + Caster) |
| **Primary Brain** | M5 Core 2 + ESP32-C3 + STM32 | Raspberry Pi 4B |
| **Microcontroller**| (Distributed above) | ESP32-S3 |
| **Sensors** | Custom 5x4 Grid (1-Wire Protocol) | 10x IR Sensors (2x 5-Channel TCRT5000, 10 Digital GPIOs) |
| **Vision** | None / CNN over IR Grid | Raspberry Pi Camera |

## 3. Starting from Scratch: Development Strategy

Because the hardware paradigm has shifted from omnidirectional to differential, and the sensor protocol has changed from 1-Wire to standard digital GPIO, **we are rewriting the codebase from scratch.**

### Step 3.1: Repository Restructuring
- **Archive v1 Code:** Legacy code (e.g., `BreadboardTest`, `MecanumWebControl`, `MC4-Advanced`) will be kept for reference but deprecated.
- **New Directory Structure:** We will create distinct folders for the Raspberry Pi and ESP32-S3:
  - `/v2_pi_core/`: Python-based logic for the Pi 4B (Camera Vision, High-Level Navigation).
  - `/v2_esp32_firmware/`: C++ / Arduino code for the ESP32-S3 (Motor PWM, PID loops, TCRT5000 reading).

### Step 3.2: ESP32-S3 Firmware (Real-Time Control)
- **Sensor Reading:** Drop the old `WeOneWire` library. Implement standard `digitalRead()` for the 10 pins of the two TCRT5000 arrays.
- **Motor Control:** Implement a differential drive mixer (Left/Right speeds) rather than mecanum kinematics. We will use hardware timers/PWM on the ESP32-S3 to drive the new motor driver.
- **Communication Bridge:** Establish a fast Serial or UART/USB protocol between the ESP32-S3 and the Raspberry Pi 4B.

### Step 3.3: Raspberry Pi 4B (High-Level AI & Vision)
- **Vision System:** Use OpenCV to process frames from the Raspberry Pi Camera, allowing us to detect intersections, green dots, and obstacles far ahead of the physical IR sensors.
- **Sensor Fusion:** Combine the fast, binary data from the ESP32-S3's TCRT5000 array with the predictive vision data from the Pi Camera.
- **Strategy & Telemetry:** Host the WebSocket telemetry dashboard on the Pi 4B (instead of the ESP) for more processing power and richer UI capabilities.

## 4. Next Immediate Steps
1. **Define ESP32-S3 Pinout:** Determine exactly which GPIO pins connect to the 10 TCRT5000 outputs and the dual motor driver.
2. **Setup Base ESP32-S3 Project:** Initialize a clean PlatformIO or Arduino project for the v2 chassis.
3. **Write Motor & Sensor Drivers:** Implement the new 2-wheel PID controller and 5-channel sensor array reader.
4. **Setup Raspberry Pi Communication:** Program the serial packet structure so the Pi can request sensor states and command motor speeds.
