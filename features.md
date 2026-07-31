# 🛠️ TEMUv2.5 COMPLETE MASTER FEATURES & ARCHITECTURE SPECIFICATION

This master specification documents all hardware, software, vision algorithms, AI acceleration, and sensor fusion features designed for the **TEMUv2.5** RoboCup Junior Rescue Line robot.

---

## 1. Perception & Dual-Camera Architecture

```
===================================================================================
                         TEMUv2.5 DUAL-CAMERA DOCKER ARCHITECTURE
===================================================================================
 [ Downward PiCamera (CSI) ]                     [ MaixCAM Pro (Edge AI Smart Cam) ]
 (Looks straight down at line)                  (Evacuation Zone & Spatial AI)
              |                                                 |
              v                                                 v
  (OpenCV Contours + Moments)                      (YOLO v8 Victim Ball Detection)
  (CatBot CutMaskWithLine)                         (Bird's-Eye View Perspective)
  (Overengineering² POI Horizon Crop)              (Built-in IMU Zero-Drift Filter)
  (Lighter RK4 Chord Predictor)                                 |
              |                                                 v
              |                                  [ Array of X Ultrasonic Sensors ]
              |                                      (HC-SR04 Obstacle Avoidance)
              +-----------------------+-------------------------+
                                      |
                                      v
                       [ RASPBERRY PI 4B DOCKER CONTAINER ]
                       (Standardized Debian Environment + VENV)
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
  [ 2x IBT_2 Drivers ]                                  [ 4x Metal Gear Servos ]
 (High-Torque Tank Drive)                              (GPIO 17, 27, 22, 23 DMA PWM)
```

### A. Downward PiCamera (CSI) — Line Tracking Subsystem
- **Downward Feed:** Mounted underneath looking straight down at the line, illuminated by white LED strips.
- **Horizon Cropping (Local Noise Filtering):** Crops out the bottom 25%–30% of the image. Evaluates line trajectory across the upper horizon (`top_mean`) and entry point (`bottom_point`). S-curves and small zig-zags cancel out to **0° (Straight Ahead)**.
- **Bounding-Box Chord Shortcutting (Racing Lines):** On 90° stair-step tiles, connects line entry and exit points with a single hypotenuse vector (chord), taking a smooth racing line around corners instead of 3 jerky right angles.
- **Lighter RK4 Kinematics Integrator:** Merges `cv2.findContours` centroid math with a 4th-Order Runge-Kutta numerical solver for ultra-smooth motor steering.

### B. MaixCAM Pro (Edge AI Smart Camera + Built-in IMU)
- **Onboard NPU Acceleration:** Processes **YOLO v8** ball detection (Silver & Black victims) at 60+ FPS locally, freeing up 100% of Raspberry Pi 4B CPU.
- **Bird's-Eye View Perspective Transformation:** Converts angled front video feed into a top-down grid map to eliminate camera distortion near room corners.
- **Built-in 6-Axis IMU with Zero-Drift Stationary Locking:**
  - Combines Gyroscope angular rate with Accelerometer gravity vectors via a Complementary Filter.
  - **Zero-Motion Lock:** When Pi motors report `speed == 0`, gyro bias is locked/zeroed, eliminating Yaw drift over long competition runs.
  - **Pitch Axis Incline Boost:** When Pitch > 10° (ramp incline), motor power is dynamically boosted to prevent rolling backward.
- **Telemetry Interface:** Transmits lightweight JSON telemetry packets over UART (`/dev/ttyS0` or USB-Serial) to the Pi.

### C. Obstacle Detection Array
- Array of **HC-SR04 Ultrasonic Sensors** mounted around the chassis for multi-angle distance measurement and water bottle detour navigation.

---

## 2. Green Marker & Intersection Reaction Engine

| Feature | **CatBot-Neo** | **Overengineering²** | **TEMUv2.5 (Selected Hybrid)** |
| :--- | :--- | :--- | :--- |
| **Detection Speed** | OpenCV HSV (`cv2.inRange`) | Numba JIT HSV (`@njit`) | **Numba JIT HSV** (Fastest execution) |
| **Validation / Anti-Noise** | Contour area & position checking | **4-Side Probing:** Probes 4 small ROIs (Top, Bottom, Left, Right) around green box for black line presence | **Overengineering 4-Side Probing** (Zero false green triggers) |
| **Intersection Transformation** | **`CutMaskWithLine`:** Slices binary mask with a line equation to block out false branches | Horizon POI boundary masking | **CatBot `CutMaskWithLine`** (Cleanest line transformation) |
| **Turn Execution** | Sequential `time.sleep` / step commands | Shared-memory timer + Gyro/IMU locked spin | **MaixCAM IMU-Heading Locked Spin** (Exact 90°/180° turns) |

---

## 3. Drive Train & Physical Hardware

- **Drive System:** 4WD High-Torque Skid-Steer / Tank-Drive using **2x IBT_2 43A Motor Drivers**.
- **Wheel Technology:** **Custom Neoprene Disc Wheels** (High-friction rubber/foam discs on aluminum hubs). *No omniwheels used due to slippage on 25° ramps.*
- **Servo Actuators:** 4 Metal Gear Servos (Claw, Lift, Gate, Cam) driven directly by Pi **GPIO 17, 27, 22, 23** using `gpiozero` DMA Soft-PWM (1µs resolution).
- **Power Management:** XL4016 High-Current Buck Regulator (5V/6V) dedicated to servos + LiPo low-voltage alarm (~10.4V threshold).

---

## 4. Software Environment & Containerization

- **Simulated Docker Container + VENV:** Standardized `Dockerfile` & `docker-compose.yml` deployed on Raspberry Pi 4B with Python Virtual Environment (VENV).
- **Hardware Passthrough:** Passes `/dev/gpiomem`, `/dev/i2c-1`, and V4L2 camera nodes (`/dev/video*`) for isolated, reproducible execution.
