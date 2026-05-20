# Project Feature & Development Log

## [2026-05-20] - Advanced Perception & Encoder-less Steering

### 1. Hybrid Perception Engine (`AI_Goal.py`)
- **Neural Classification**: Implemented a localized CNN for real-time 4x5 grid pattern recognition.
- **Topological Analysis**: Added BFS-based connected component analysis as a deterministic fallback for intersection detection.
- **Vector Extraction (PCA)**: Developed a Principal Component Analysis module to extract mathematical line vectors (heading and offset) directly from raw sensor pixels.

### 2. Encoder-less Orientation Logic
- **Visual Compass**: Replaced traditional wheel odometry with a "Visual Compass" system that calculates robot heading relative to the physical track geometry.
- **Proportional Instruction Steering**: Introduced dynamic steering correction calculated as $Kp \times (\text{Target} - \text{Visual Heading})$.
- **"Seek and Catch" Maneuvers**: Developed a state-machine logic for $90^\circ$ turns that uses visual patterns to trigger the "end of turn" rather than pulse counts.

### 3. Fused Perception (AI + MPU6050)
- **Primary Truth**: Visual AI Vector logic.
- **Secondary Backup**: MPU6050 Inertial Yaw monitoring.
- **Dynamic Braking**: Implemented a "Precision Catch" system that slows pivot rotation as the AI Vector aligns with the target line, preventing overshoots.

### 4. Quad-Motor Kinematic Synchronization
- **Independent Channel Mapping**: Configured independent control for all 4 motors (FL, FR, RL, RR).
- **Power Bias Correction**: Introduced a software `Bias` parameter to compensate for physical motor variances and friction without requiring hardware encoders.
- **Visual Traction Control**: Leverages the AI Engine's error detection to auto-correct the trajectory if a single wheel slips.

---
*End of Log entry for 2026-05-20*
