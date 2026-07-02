# Raspberry Pi 4B Computer Vision & Navigation Architecture

## 1. System Overview
The Raspberry Pi 4B acts as the high-level brain of the DPSI-LFR V2 autonomous robot. Running Python 3 with OpenCV, the Pi 4B processes video feeds from an onboard Raspberry Pi Camera module mounted at a 20-degree downward tilt. It identifies navigation markers (such as Green Dots at intersections), computes spatial relationships, handles complex obstacle avoidance and rescue zone strategies, and sends high-level motion directives to the ESP32-S3 via USB Serial (`/dev/ttyUSB0`).

---

## 2. 20-Degree Camera Tilt Rectification & Perspective Warp Logic

Mounting the camera at a downward pitch angle of $\alpha = 20^\circ$ captures a forward view of the track, but introduces keystone perspective distortion where parallel lines converge in the image plane. To restore accurate metric spatial geometry for contour analysis, an inverse perspective transform (bird's-eye view warp) is applied to every captured frame.

### 2.1 Geometric Perspective Rectification Model

```
Side View (Physical Camera Setup):
        Camera Axis
           \  20° Tilt
            \
             \
--------------+--------------------- Track Ground Plane
              |<--- Trapezoid ROI --->|

Image Plane Distortion vs. Rectified Bird's-Eye View:
  Tilted Camera Frame (Trapezoid)          Rectified Perspective Frame (Rectangle)
     (x1,y1)         (x2,y2)                  (0,0)               (W_dst, 0)
        +---------------+                        +-------------------+
       /                 \                       |                   |
      /                   \       Warp           |                   |
     /                     \   =========>        |                   |
    +-----------------------+                    +-------------------+
  (x4,y4)                 (x3,y3)              (0, H_dst)        (W_dst, H_dst)
```

### 2.2 Homography Matrix Formulation

The planar perspective transformation maps points $(x, y)$ in the original distorted frame to $(x', y')$ in the rectified bird's-eye view frame using a $3 \times 3$ Homography Matrix $M$:

$$\begin{bmatrix} x_i \cdot w \\ y_i \cdot w \\ w \end{bmatrix} = M \cdot \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} m_{00} & m_{01} & m_{02} \\ m_{10} & m_{11} & m_{12} \\ m_{20} & m_{21} & m_{22} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$

$$x' = \frac{m_{00}x + m_{01}y + m_{02}}{m_{20}x + m_{21}y + m_{22}}, \quad y' = \frac{m_{10}x + m_{11}y + m_{12}}{m_{20}x + m_{21}y + m_{22}}$$

#### Empirical Calibration Coordinates (Resolution: $640 \times 480$):
- **Source Points (`src`)**: 4 corners defining the ground trapezoid visible in the lower half of the frame:
  $$\text{src} = \begin{bmatrix} (180, 260) & (460, 260) & (600, 460) & (40, 460) \end{bmatrix}^T$$
- **Destination Points (`dst`)**: Rectangular target grid ($400 \times 400$ metric view):
  $$\text{dst} = \begin{bmatrix} (0, 0) & (400, 0) & (400, 400) & (0, 400) \end{bmatrix}^T$$

The constant matrix $M = \text{cv2.getPerspectiveTransform(src, dst)}$ is pre-computed during startup initialization to eliminate runtime matrix inversion overhead.

---

## 3. OpenCV Processing Pipeline for Green Dot Intersection Detection

Green Dots indicate mandatory turn directions at track intersections according to standard RoboCup Junior / DPSI rules. The computer vision pipeline executes sequentially per frame:

```
+------------------+     +------------------------+     +----------------------+
| Frame Capture    | --> | Inverse Perspective    | --> | BGR to HSV Color     |
| (640x480 @ 30fps)|     | Warp Transformation    |     | Space Conversion     |
+------------------+     +------------------------+     +----------------------+
                                                                   |
                                                                   v
+------------------+     +------------------------+     +----------------------+
| Spatial Decision | <-- | Contour Extraction &   | <-- | HSV Thresholding &   |
| Logic Matrix     |     | Bounding Box Filtering |     | Morphological Filter |
+------------------+     +------------------------+     +----------------------+
```

### 3.1 Pipeline Step Breakdown

#### Step 1: Image Capture & Rectification
Raw video frames are read from the camera pipeline, resized to $640 \times 480$, and warped using `cv2.warpPerspective(frame, M, (400, 400))`.

#### Step 2: Color Space Conversion & HSV Thresholding
The image is converted from BGR to HSV space to isolate green hue components independent of ambient lighting changes.
- **Green Lower HSV Bound**: `[35, 80, 80]`
- **Green Upper HSV Bound**: `[85, 255, 255]`
- **Black Line Lower HSV Bound**: `[0, 0, 0]`
- **Black Line Upper HSV Bound**: `[180, 255, 50]`

Binary masks are generated using `cv2.inRange()`. Morphological operations (`cv2.morphologyEx` with a $5 \times 5$ ellipse kernel) remove noise pixels (`MORPH_OPEN`) and close small internal voids (`MORPH_CLOSE`).

#### Step 3: Contour Extraction & Area Filtering
`cv2.findContours()` extracts external boundaries on the green binary mask. Contours are filtered based on geometric area constraints:

$$A_{min} \le \text{ContourArea}(C) \le A_{max} \quad (A_{min} = 300\text{ pixels}^2, A_{max} = 5000\text{ pixels}^2)$$

#### Step 4: Spatial Decision Matrix Logic
For each valid green contour, its centroid $(\bar{x}, \bar{y})$ and bounding box are evaluated relative to the main black line bounding region detected in the same rectified frame:

```
           [ Rectified Frame Top-Down View ]
           
                      | Black Line |
                      |   (x_line) |
                      |            |
   (Left Green Dot)   |            |   (Right Green Dot)
     [ centroid_X ]   |            |     [ centroid_X ]
     < x_line - offset|            |     > x_line + offset
                      |            |
```

| Detected Green Contour Spatial Pattern | Intersection Decision Outcome | Master Action Dispatched to ESP32 |
| :--- | :--- | :--- |
| Single green dot located to the **Left** of the black line ($\bar{x} < x_{line} - \delta$) | **Left Turn Intersection** | Issue `EXECUTE_TURN_90(DIR_LEFT)` serial command. |
| Single green dot located to the **Right** of the black line ($\bar{x} > x_{line} + \delta$) | **Right Turn Intersection** | Issue `EXECUTE_TURN_90(DIR_RIGHT)` serial command. |
| Two green dots located on **both Left and Right** sides of the black line | **U-Turn (180° Spin)** | Issue `EXECUTE_TURN_180()` serial command. |
| Green dot placed directly on top of line with no continuing track ahead | **False Marker / Dead End** | Maintain line following or initiate search. |

---

## 4. Master Navigation State Machine Architecture

The high-level autonomous navigation software on the Raspberry Pi 4B is structured as an asynchronous Finite State Machine (FSM).

### 4.1 State Transition Diagram

```
                       +-----------------------+
                       |  STATE_LINE_FOLLOWING | <-------------------+
                       +-----------+-----------+                     |
                                   |                                 |
        Green Dot Intersection     | Obstacle Distance               | Turn / Avoidance
        Detected                   | < 15cm Detected                 | Complete
                                   v                                 |
    +------------------------------+-----------------------------+   |
    |                                                            |   |
    v                                                            v   |
+-------------------------------+              +---------------------+----+
| STATE_INTERSECTION_DECISION   |              | STATE_OBSTACLE_AVOIDANCE |
+---------------+---------------+              +---------------------+----+
                |                                                    |
                | Rescue Zone Entrance Marker Detected               |
                v                                                    |
+---------------+----------------------------------------------------+----+
| STATE_RESCUE_ZONE_NAVIGATION                                            |
+-------------------------------------------------------------------------+
```

---

### 4.2 State Descriptions & Operational Protocols

#### 1. `STATE_LINE_FOLLOWING` (Default Operational State)
- **Behavior**: The Pi 4B monitors camera feeds for markers while letting the ESP32-S3 run its autonomous high-speed 100Hz PID loop. The Pi streams telemetry updates and verifies track continuity.
- **Transition Triggers**:
  - Transition to `STATE_INTERSECTION_DECISION` if green dot contours are identified.
  - Transition to `STATE_OBSTACLE_AVOIDANCE` if forward ToF/Ultrasonic sensor reports obstacle distance $< 15\text{ cm}$.
  - Transition to `STATE_RESCUE_ZONE_NAVIGATION` if silver/reflective rescue entrance line is detected.

#### 2. `STATE_INTERSECTION_DECISION`
- **Behavior**: Upon detecting a green dot, the Pi overrides ESP32 line following by sending a slow-down serial packet (`SET_SPEED_BASE(80)`). It validates the green dot over 3 consecutive frames to prevent transient noise triggers. Once confirmed, it issues the precise turn command (`EXECUTE_TURN_90` or `EXECUTE_TURN_180`) and waits for the ESP32 `TURN_COMPLETE` telemetry acknowledgment.
- **Transition Trigger**: Returns to `STATE_LINE_FOLLOWING` after turn completion confirmation.

#### 3. `STATE_OBSTACLE_AVOIDANCE`
- **Behavior**: Executed when an obstacle blocks the line. The Pi executes a deterministic orbit maneuver:
  1. Issues `EXECUTE_TURN_90(DIR_LEFT)` (or right depending on clear path).
  2. Issues `DRIVE_DISTANCE(25cm)` forward parallel to obstacle.
  3. Issues `EXECUTE_TURN_90(DIR_RIGHT)` to clear obstacle.
  4. Drives forward until the front 10-IR array on the ESP32 re-detects the main black line.
- **Transition Trigger**: Line acquisition confirmed by ESP32 sensor telemetry returns system to `STATE_LINE_FOLLOWING`.

#### 4. `STATE_RESCUE_ZONE_NAVIGATION`
- **Behavior**: Enters when reaching the victim rescue arena. The vision system switches from line/dot detection to object detection (spherical tennis balls / rescue elements). Employs systematic grid search algorithms and controls gripper/actuator sub-modules (if equipped) while keeping track of exit wall locations.
- **Transition Trigger**: Mission completion or exit portal alignment.
