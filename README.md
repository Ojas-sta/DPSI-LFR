# DPSI LFR V3 - Temuv2.5 (Hybrid Overengineering)

Welcome to the **DPSI LFR V3** repository (`dpsi_lfr_v3` branch). This branch contains the finalized architectural plans and documentation for our next-generation autonomous mobile robot.

## Project Overview

The DPSI LFR V3 has been upgraded to the **Temuv2.5 (Hybrid Overengineering)** architecture. We have combined the high-speed multi-core multiprocessing model from *Overengineering-squared-RoboCup* with the advanced numerical kinematics (RK4) and 3D obstacle avoidance of *TemuFollower*.

### Core Capabilities
- **90 FPS Multi-Process Line Following**: Zero-copy IPC (`multiprocessing.shared_memory`) decoupling Pi Camera processing from motor control.
- **Dedicated Sensor Processing**: 
  - **Pi Camera (CSI)**: Handles high-speed line tracking exclusively.
  - **Intel RealSense D435**: Handles 3D depth obstacles and Evacuation Zone ball alignment.
- **Low-Level Actuation**: ESP32 DevKit V1 acting as a strict real-time motor controller and hardware safety watchdog over 115200 baud UART.
- **Power & Motors**: **2x IBT_2 Motor Drivers** (BTS7960-based) capable of delivering massive high-current PWM safely, connected to the ESP32.

## Documentation

Please explore the `architecture/` folder for our extensive, updated markdown documents featuring Mermaid diagrams and flowcharts:
- [`architecture/system_architecture.md`](architecture/system_architecture.md): Hardware topology, UART Protocol, and Power Distribution.
- [`architecture/software_architecture.md`](architecture/software_architecture.md): Multi-process OS layout and algorithm pipelines.
- [`architecture/implementation_plan.md`](architecture/implementation_plan.md): The execution roadmap.

## Tech Stack
- **OS**: Embedded Linux
- **High-Level Compute**: Raspberry Pi 4B (Python Multiprocessing, OpenCV, Numba JIT)
- **Low-Level Compute**: ESP32 (C++, FreeRTOS, PlatformIO)
- **Actuators**: 2x IBT_2 Motor Drivers
