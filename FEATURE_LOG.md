# Project Feature & Development Log

## [2026-05-20] - Distributed Intelligence & MC4.0 Platform Transition

### 1. Hardware Platform: MC4.0 Chassis Integration
- **Chassis**: Migration to the professional **MC4.0 Industrial Chassis**, providing superior structural rigidity and modular stacking.
- **Drive System**: Integrated **4x DC Encoder Motors** for high-precision closed-loop feedback.
- **Traction**: Equipped with **Mecanum Wheels** for omnidirectional movement capability.

### 2. Distributed Project Architecture (Triple-Processor)
Successfully implemented a distributed computing model to optimize real-time performance:
- **M5 Core 2 (The Brain)**: Handles high-level AI (CNN/PCA), path strategy, and WebSocket telemetry server.
- **ESP32 C3 Super Mini (The Eyes)**: Dedicated "Sensor Pod" controller. Performs high-speed 1-Wire bit-banging for the 5x4 IR grid and streams data via 230,400 baud UART.
- **STM32 Module (The Muscles)**: 4-channel independent motor controller. Handles low-level PWM and PID loops for the encoder motors via I2C (Address `0x24`).

### 3. Hybrid Perception Engine (`AI_Goal.py`)
- **Neural Classification**: Implemented a localized CNN for real-time 4x5 grid pattern recognition.
- **Topological Analysis**: Added BFS-based connected component analysis as a deterministic fallback for intersection detection.
- **Vector Extraction (PCA)**: Developed a Principal Component Analysis module to extract mathematical line vectors (heading and offset) directly from raw sensor pixels.

### 4. Encoder-less Orientation Logic (Visual Compass)
- **Concept**: Replaced traditional wheel odometry with a "Visual Compass" system that calculates robot heading relative to the physical track geometry.
- **Proportional Instruction Steering**: Introduced dynamic steering correction calculated as $Kp \times (\text{Target} - \text{Visual Heading})$.
- **"Seek and Catch" Maneuvers**: Developed a state-machine logic for $90^\circ$ turns that uses visual patterns to trigger the "end of turn" rather than pulse counts.

### 5. Fused Perception (AI + MPU6050)
- **Primary Truth**: Visual AI Vector logic.
- **Secondary Backup**: MPU6050 Inertial Yaw monitoring.
- **Dynamic Braking**: Implemented a "Precision Catch" system that slows pivot rotation as the AI Vector aligns with the target line, preventing overshoots.

---
*End of Log entry for 2026-05-20*
