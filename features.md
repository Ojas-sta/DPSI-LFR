# 🛠️ TEMUv2.5 FEATURES & ARCHITECTURE SPECIFICATION

This document details all key vision, kinematic, hardware, and intersection features for the **TEMUv2.5** RoboCup Junior Rescue Line robot, comparing **CatBot-Neo** and **Overengineering²** solutions.

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

## 2. Green Marker Reaction Logic Comparison (Raspberry Pi 4B)

| Feature | **CatBot-Neo** | **Overengineering²** | **TEMUv2.5 (Selected Hybrid)** |
| :--- | :--- | :--- | :--- |
| **Detection Method** | OpenCV HSV Thresholding (`cv2.inRange`) | Numba JIT HSV Masking (`@njit`) | Numba JIT HSV Masking |
| **Validation Method** | Contour counting & geometric area | **4-Side Probing:** Checks Top/Bottom/Left/Right ROIs around green box for black line presence | **Overengineering 4-Side Probing** (Eliminates false green triggers) |
| **Intersection Slicing** | **`CutMaskWithLine`:** Slices binary mask to block off false branches | Mask cropping via POI boundary points | **CatBot `CutMaskWithLine`** (Cleanest line transformation) |
| **Turn Execution** | Sequential `time.sleep` / step commands | Shared-memory timer + Gyro/IMU locked spin | **IMU-Heading Locked Spin** (Exact 90°/180° rotation) |

---

## 3. Hardware Query: Do Overengineering² Use Omniwheels?

**NO. Overengineering² does NOT use omniwheels.**

Directly from their official repository specifications (`robot_v.3/README.md`):
- They use **4x Custom Neoprene Wheels** (Neoprene rubber/foam discs mounted on aluminum hubs) in a standard **4WD Skid-Steer / Tank Drive** configuration.
- **Why No Omniwheels?** Omniwheels slip severely on 25° competition ramps, speed bumps, and smooth rescue tiles. Neoprene rubber discs provide maximum friction, high torque climbing power, and zero wheel-slip under high acceleration.

---

## 4. Environment & Compute Architecture

- **Primary Compute:** Raspberry Pi 4B (64-bit OS / Debian Trixie).
- **Containerization:** Docker Container + Python VENV (`Dockerfile` + `docker-compose.yml`) exposing `/dev/gpiomem` and `/dev/i2c-1`.
- **Dual Camera Setup:**
  - **Downward PiCamera (CSI):** Line tracking, horizon cropping, and green markers.
  - **Front USB Camera:** Evacuation Zone victim ball detection & alignment.
- **Actuators:** 2x IBT_2 43A Motor Drivers + 4 Metal-Gear Servos on **GPIO 17, 27, 22, 23** (`gpiozero` DMA Soft-PWM).
