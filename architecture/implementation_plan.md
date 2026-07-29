# Goal Description

Rewrite the Temuv2 software architecture to create **Temuv2.5 (Hybrid Overengineering)**. We are adopting a 5-process shared memory model from *Overengineering-squared-RoboCup* while retaining the advanced RK4 (and RK15) kinematics and 3D obstacle avoidance from *TemuFollower*. 

The objective is to achieve a 90 FPS line-tracking control loop on the Raspberry Pi 4B. The architecture has now been expanded to include a **CustomTkinter GUI**, **RealSense IMU Sensor Fusion**, and **Slope Detection** for advanced terrain traversal.

## User Review Required

> [!IMPORTANT]
> The implementation plan below reflects the new additions you requested. Please review the "Proposed Changes" and "Open Questions" sections to ensure they match your expectations. If everything looks good, approve it and I will commit the architectural changes and restore the deprecated archive.

## Open Questions

> [!NOTE]
> 1. **Sensor Fusion Math**: The RealSense D435i outputs raw Gyro and Accel data. Should we run a standard Madgwick filter inside `realsense_proc.py` to calculate the `[Pitch, Roll, Yaw]` Euler angles, and pass those floats to the `control_proc.py`? (Recommended: Yes, it offloads math from the control loop).
> 2. **Slope Detection Reaction**: When the robot detects a ramp (e.g., Pitch > 15 degrees), should the `control_proc.py` automatically shift into a "High-Torque / Low-Speed" mode and temporarily disable aggressive RK4 turning to prevent slipping? (Recommended: Yes).
> 3. **Deprecated Archive**: In our last git push, I permanently deleted the old unused files. Would you like me to `git revert` that commit to bring them back, and then neatly move them into a `deprecated_archive/` folder instead? (Recommended: Yes, to preserve history).

## Proposed Changes

### Multiprocessing Framework (Zero-Copy IPC)
#### [MODIFY] [mp_manager.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/mp_manager.py)
- Expand the fixed-size C-style float array to include IMU telemetry: `[LineError, LineAngle, DistanceToWall, BallX, BallY, Pitch, Roll, Yaw]`.

### Vision & Sensor Processes
#### [MODIFY] [realsense_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/realsense_proc.py)
- **NEW**: Subscribe to the D435i's built-in IMU streams (Gyro and Accel).
- **NEW**: Implement a sensor fusion algorithm (Complementary or Madgwick filter) to continuously compute the robot's Pitch and Roll angles in 3D space.

#### [NEW] [line_cam_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/line_cam_proc.py)
- Uses `Picamera2` at 448x252. Extracts 4-8 ROIs, computes centroids with Numba JIT.

#### [NEW] [evac_cam_opencv.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/evac_cam_opencv.py) & [evac_cam_yolo.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/evac_cam_yolo.py)
- Swappable modules for Evac Zone ball detection.

### Control & Communications
#### [MODIFY] [control_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/control_proc.py)
- **NEW**: Implement **Slope Detection** logic. If the Pitch from shared memory exceeds the ramp threshold, dynamically alter the motor mapping limits to prioritize traction and torque.
- Implements both RK4 and RK15 integration modes.

#### [NEW] [serial_io_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/serial_io_proc.py)
- Standard UART loop to the ESP32 and 2x IBT_2 drivers.

### Graphical User Interface (5th Process)
#### [NEW] [gui_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/gui_proc.py)
- Build a sleek, modern UI using **CustomTkinter** (dark mode, rounded corners).
- This process will read asynchronously from the `mp_manager` shared memory and display real-time gauges: Line Error, Obstacle Distance, IMU Pitch/Roll, and current State.
- Because it is a separate OS process, the blocking `mainloop()` will not affect the 90 FPS control loop.

## Verification Plan

### Automated Benchmarking
- We will measure the latency difference between the OpenCV and YOLO11n Evac Zone pipelines.
- Verify that `gui_proc.py` CPU usage stays below 20% on a single core.

### Manual Verification
- Physically tilt the robot and observe the CustomTkinter GUI displaying the IMU Pitch in real-time.
- Confirm the motors automatically adjust their RPM profiles when a slope is detected.
