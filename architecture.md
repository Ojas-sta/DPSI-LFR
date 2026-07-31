# 🏛️ TEMUv2.5 SYSTEM ARCHITECTURE SPECIFICATION
**RoboCup Junior Rescue Line International Competition Robot**

---

## 1. System Overview & Core Philosophy

The **TEMUv2.5** is an overengineered, high-speed, high-torque autonomous robot designed for the RoboCup Junior Rescue Line competition. It combines **Edge AI perception**, **Numba JIT RK4 kinematic math**, **Overengineering² Horizon Cropping**, **CatBot-Neo Intersection Mask Slicing**, **heavy-duty IBT_2 motor drivers**, and **Docker containerization**.

```
===================================================================================
                         TEMUv2.5 DUAL-CAMERA DOCKER ARCHITECTURE
===================================================================================
 [ Downward PiCamera (CSI) ]                     [ Forward MaixCAM Pro (NPU+IMU) ]
 (Looks straight down at line)                  (YOLO Ball Detection, Bird's-Eye,
              |                                  IMU Complementary Filter, Sorting Servo)
              v                                                 |
  (OpenCV Contours + Moments)                                   | (UART / USB Serial)
  (CatBot CutMaskWithLine)                                      v
  (Overengineering² POI Horizon Crop)            [ Array of X Ultrasonic Sensors ]
  (Lighter RK4 Chord Predictor)                      (HC-SR04 Obstacle Avoidance)
              |                                                 |
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

---

## 2. Complete Hardware Architecture

### A. Compute & AI Acceleration
1. **Primary Compute:** Raspberry Pi 4B (64-bit OS / Debian Trixie) running inside a **Docker Container + VENV**.
2. **Edge AI & IMU Processor:** **MaixCAM Pro** (Sipeed NPU edge camera) mounted forward-facing.
   - Runs **YOLO v8** ball detection (Silver & Black victims) at 60+ FPS locally.
   - Executes **Bird's-Eye View (Perspective Transform)** to eliminate camera perspective distortion in corners.
   - Houses the onboard **6-axis IMU** (Gyro + Accelerometer).
   - Directly controls the **Sorting Servo** to route Silver vs Black balls into separate internal chutes upon pickup.

### B. Cameras & Distance Sensors
1. **Downward Line Camera:** Downward-facing **Raspberry Pi Camera (CSI)** illuminated by an array of white COB LEDs.
2. **Distance Sensing:** Array of **HC-SR04 Ultrasonic Sensors** (Front & Side) for obstacle detection.

### C. Actuators, Drive Train & Wheels
1. **Drive Motors & Drivers:** 4x 12V DC Geared Motors powered by **2x IBT_2 43A Motor Drivers** connected directly to Raspberry Pi GPIOs for skid-steer/tank drive.
2. **Wheels:** **4x Custom High-Traction Neoprene Discs on Aluminum Hubs** (4WD Skid-Steer / Tank Drive).
   - *Design Choice:* Omniwheels are **explicitly excluded** because their lateral rollers slip uncontrollably on 25° competition ramps and speed bumps.
3. **Servos (4x Pi GPIO + 1x MaixCAM):**
   - **Pi Controlled:** 4 Metal-Gear Servos (Claw, Lift, Gate, Cam) controlled via `gpiozero` DMA Soft-PWM directly on **GPIO 17, 27, 22, 23** (1µs resolution, PCA9685 eliminated).
   - **MaixCAM Controlled:** 1 Sorting Servo for routing Silver vs Black balls.

### D. Power & Regulation Subsystem
1. **Main Battery:** 7.4V/11.1V LiPo Battery with built-in low-voltage buzzer alarm (~10.4V threshold).
2. **Voltage Regulation:**
   - **5.2V Regulator:** Dedicated to Raspberry Pi 4B.
   - **XL4016 High-Current Buck Converter (5V/6V):** Dedicated to the high-torque servo array.
   - **Motor Supply (10V-12V):** Direct regulated rail to IBT_2 motor drivers.

---

## 3. Comprehensive Software Architecture & Algorithms

### A. Containerization & Simulation Environment
- **Docker Container + Python VENV**: Standardized `Dockerfile` and `docker-compose.yml` deploying a clean Python Virtual Environment (VENV) on the Pi 4B, exposing `/dev/gpiomem`, `/dev/i2c-1`, and V4L2 camera nodes (`/dev/video*`).

### B. Downward Line Follower (Horizon Crop + Racing Line RK4)
1. **OpenCV Contours & Moments:** `cv2.findContours` and `cv2.moments` extract line mass centroids and direction vectors.
2. **Overengineering² Horizon Crop (Noise Cancellation):** Crops out the bottom 25%–30% of the image (where local zig-zag noise occurs). Evaluates line trajectory across the upper horizon (`top_mean`) and entry boundary (`bottom_point`). S-curves and small zig-zags cancel out to **0° (Straight Ahead)**.
3. **Bounding-Box Chord Shortcutting (Racing Lines):** On 90° stair-step turns, the algorithm connects the entry point to the exit point with a single hypotenuse vector (chord), taking a smooth single-arc **racing line** across the turn.
4. **Lighter RK4 Kinematics Integrator:** Integrates contour trajectory vectors into a lightweight 4th-Order Runge-Kutta numerical solver for predictive steering.

### C. Green Marker & Intersection Engine
1. **Overengineering² 4-Side Probing:** When a green HSV contour is detected, the algorithm probes 4 small ROIs around the green box (**Top, Bottom, Left, Right**) to verify black line touch points. Eliminates 100% of false green triggers from ambient lighting.
2. **CatBot-Neo `CutMaskWithLine`:** Slices the binary image mask across intersection entry points, converting complex 4-way or T-intersections into perceived straight lines or clean single turns.
3. **IMU Heading-Locked Spin:** Executes timed/heading-locked turns (90°/180°) until the downward PiCamera re-acquires the main black line.

### D. Zero-Drift IMU Complementary Filter
1. **Gyro + Accelerometer Integration:** Fuses Gyroscope angular rate with Accelerometer gravity vectors.
2. **Stationary Drift Lock:** When Pi motor `speed == 0`, gyro bias is locked/zeroed, eliminating Yaw drift over long competition runs.
3. **Pitch Incline Boost:** Dynamically increases motor PWM when Pitch > 10° on ramps.

### E. Obstacle Avoidance & Reverse Recovery Net
1. **0.25s Time-Averaged Filtering:** Filters ultrasonic sensor readings over a 0.25s window to prevent false triggers.
2. **Camera & Ramp Verification:** Verifies object contour area and checks Pitch axis before triggering detour.
3. **Gyro-Locked 90° Box Detour:** Executes a precise 90° gyro-locked turn, side ultrasonic wall-following (15cm gap), and 90° re-entry turn.
4. **Overengineering² Reverse Recovery Net:** If the downward camera fails to re-acquire the black line within 3 seconds (`timer.get_timer("obstacle_turn")`), it triggers **`return_after_failed_obstacle()`**, reversing back to the start point to attempt the detour from the opposite side!

### F. Evacuation Zone, Sorting & Drop Logic
1. **Edge AI Victim Sorting:** MaixCAM Pro runs YOLO v8 ball detection. Upon pickup, MaixCAM actuates the **Sorting Servo** to route Silver balls into the Alive victim chute and Black balls into the Dead victim chute.
2. **Pre-Recorded Servo Sequences:** Hardcoded macro sequences (`APPROACH -> LOWER -> CLAW CLOSE -> LIFT HIGH`).
3. **Rear-Entry Platform Alignment:** Uses IMU Yaw heading to align the rear of the robot 180° square with the target Green/Red Evacuation platform.
4. **CatBot-Neo 12-Cycle Violent Motor Shake Routine:** Upon opening the rear gate servo, the robot executes a **12-cycle rapid motor jerk sequence** (forward `100, 100` for 150ms, backward `-100, -100` for 250ms) to force all balls to roll out of the chute onto the platform without jamming.

---

## 4. Hardware & Software Workflows

### A. Hardware Tasks (Vatsal) — *Approval: OjasP & Shubham Sir*
1. **Buck Converter:** Acquire and wire XL4016 buck converter for servos.
2. **Pi Camera Mounting:** Mount PiCamera on underside facing forward/down using windowsill mount.
3. **Evacuation Mechanism:** Mount evacuation zone claw, lift servos, sorting servo, and rear victim storage compartment.
4. **Arena Ramp:** Coordinate ramp incline (max 30°) and white border tiles to prevent floor detection false positives.
5. **Status LEDs & Buzzer:** Finalize Big Green LED, Big Red LED, and Piezo Buzzer hardware integration.

### B. Software Tasks (OjasP)
1. **Docker Setup:** Create `Dockerfile` and `docker-compose.yml` on Pi 4B.
2. **Hybrid OpenCV+RK4 Line Follower:** Combine `cv2.findContours`, Overengineering² Horizon Crop, Chord Shortcutting, and CatBot-Neo `CutMaskWithLine`.
3. **MaixCAM Telemetry Driver (`core/maixcam_telemetry.py`):** Read IMU & YOLO ball alignment data over UART.
4. **Servo Driver:** Maintain `gpiozero` DMA Soft-PWM module (`hardware_tests/gpiozero_servo_test.py`) for GPIO 17, 27, 22, 23.

---

## 5. Development Milestones

| Milestone | Key Objective | Status |
| :--- | :--- | :---: |
| **Milestone 1** | High-Speed Line Tracking (PiCamera + RK4 + OpenCV Contours + Horizon Crop + IBT_2 Motors) | 🟡 In Progress |
| **Milestone 2** | Obstacle Avoidance & Green Intersection Handling (Ultrasonic Array + CatBot Masking + Reverse Safety Net) | ⚪ Planned |
| **Milestone 3** | Evacuation Zone & Victim Rescue (MaixCAM Pro YOLO + Bird's Eye View + Sorting Servo + 12-Cycle Shake Drop) | ⚪ Planned |
