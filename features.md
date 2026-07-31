# 🛠️ TEMUv2.5 FEATURES & ARCHITECTURE SPECIFICATION

This document details all key vision, kinematic, hardware, obstacle, and evacuation zone features for the **TEMUv2.5** RoboCup Junior Rescue Line robot, comparing **CatBot-Neo** and **Overengineering²** solutions.

---

## 1. Vision & Line-Following Features

### A. Horizon Cropping (Local Noise Cancellation)
- **Concept:** Crops out the bottom 25%–30% of the downward camera feed (where local zig-zag and S-curve perturbations occur).
- **Mechanism:** Evaluates line entry (`bottom_point`) and exit (`top_mean`) across the look-ahead horizon.
- **Result:** S-curves and small zig-zags cancel out to **0° (Straight Ahead)**. The robot glides straight through without twitching.

### B. Bounding-Box Chord Shortcutting (Racing Lines on 90° Step Turns)
- **Concept:** On 90° stair-step tiles, standard line followers jerk through 3 separate right angles.
- **Mechanism:** Draws a hypotenuse vector (chord) directly connecting the entry point to the far exit point (`near_high_index`).
- **Result:** Takes a smooth, single-arc **racing line** across the turn.

### C. Lighter RK4 Kinematics Integrator
- Combines OpenCV `cv2.findContours` & geometric moments with a 4th-Order Runge-Kutta (RK4) numerical solver to predict smooth trajectories and eliminate motor jitter.

---

## 2. Green Marker Reaction Logic Comparison

| Feature | **CatBot-Neo** | **Overengineering²** | **TEMUv2.5 (Selected Hybrid)** |
| :--- | :--- | :--- | :--- |
| **Detection Speed** | OpenCV HSV (`cv2.inRange`) | Numba JIT HSV (`@njit`) | **Numba JIT HSV** (Fastest execution) |
| **Validation / Anti-Noise** | Contour area & position checking | **4-Side Probing:** Probes 4 small ROIs (Top, Bottom, Left, Right) around green box to verify black line touch points | **Overengineering 4-Side Probing** (Zero false green triggers) |
| **Intersection Transformation** | **`CutMaskWithLine`:** Slices binary mask to block off false branches | Horizon POI boundary masking | **CatBot `CutMaskWithLine`** (Cleanest line transformation) |
| **Turn Execution** | Sequential `time.sleep` / step commands | Shared-memory timer + Gyro/IMU locked spin | **IMU-Heading Locked Spin** (Exact 90°/180° turns) |

---

## 3. Obstacle Handling Comparison

| Feature | **CatBot-Neo** | **Overengineering²** | **TEMUv2.5 Hybrid Strategy** |
| :--- | :--- | :--- | :--- |
| **Distance Sensing** | 1x Front Ultrasonic (HC-SR04) | 6x Pololu IR Distance Sensors | **Array of HC-SR04 Ultrasonic Sensors** |
| **Trigger Filtering** | Single distance check | **0.25s Time-Averaging Window** + Gyro Ramp Check | **0.25s Time-Averaged Window + Camera Verification** |
| **Detour Trajectory** | Open Arc Drive (`100, 30`) | **Gyro 90° Turn + Side IR Wall Following** (15cm gap) | **Gyro-Locked 90° Box Detour** |
| **Safety Net** | None (keeps spinning) | **`return_after_failed_obstacle()`:** Reverses back to start point if line is lost for >3s | **Overengineering Reverse Recovery Net** |

---

## 4. Evacuation Zone, Sorting & Drop Logic

### A. MaixCAM Pro Sorting Servo Integration
- **MaixCAM Pro NPU:** Runs YOLO v8 ball classification (Silver = Alive, Black = Dead) at 60+ FPS locally.
- **Direct Sorting Servo Control:** MaixCAM Pro directly actuates an onboard **Sorting Servo** to route Silver balls into the Alive victim chute and Black balls into the Dead victim chute upon pickup.

### B. Evacuation Zone & Victim Drop Comparison

| Feature | **CatBot-Neo** | **Overengineering²** | **TEMUv2.5 Hybrid Strategy** |
| :--- | :--- | :--- | :--- |
| **Victim Sorting** | Single top cage (All balls together) | Separate Silver/Black trapdoors | **MaixCAM Pro Sorting Servo + Separate Chutes** |
| **Drop Servo Protocol** | Hardcoded `gpiozero` Angle Macros | Hardcoded `servo_pos(id)` Macros | **Pre-Recorded Servo Sequence Macros** |
| **Alignment to Platform** | CMPS14 Compass 180° Rear Align | BNO055 Gyro 180° Rear Align | **IMU 180° Rear Gyro Alignment** |
| **Deposit Mechanism** | **12-Cycle Motor Shake Routine** (Rapid forward/backward jerks) | Dual trapdoor unlatch + ejector lever | **CatBot 12-Cycle Violent Motor Shake Routine** |

---

## 5. Hardware Specifications & Wheel Choice

- **Wheels:** **4x Custom High-Traction Neoprene / Foam Discs on Aluminum Hubs** (4WD Skid-Steer / Tank Drive).
  - *Note:* Omniwheels are **not used** because they slip sideways on 25° competition ramps and speed bumps.
- **Compute:** Raspberry Pi 4B (Docker Container + Python VENV).
- **Vision:** Downward PiCamera (CSI) + Forward MaixCAM Pro (Edge AI NPU + Built-in IMU).
- **Servos:** 4 Metal-Gear Servos (Claw, Lift, Gate, Cam) on **GPIO 17, 27, 22, 23** (`gpiozero` DMA Soft-PWM) + 1 Sorting Servo on MaixCAM Pro.
