# Project Milestones (Temuv2.5 Hybrid Overengineering)

## 1st Milestone: High-Speed Line Tracking Pipeline
- Implement the `mp_manager.py` shared memory layer for zero-copy IPC.
- Initialize `line_cam_proc.py` using Picamera2 and Numba JIT for 90 FPS ROI extraction.
- Create `serial_io_proc.py` and the ESP32 UART firmware to safely drive the 2x IBT_2 motor drivers.
- Implement the RK4 kinematics loop in `control_proc.py` for high-speed line following.

## 2nd Milestone: RealSense Integration & Obstacles
- Implement `realsense_proc.py` to stream Depth and RGB.
- Enable 10th percentile floor subtraction for physical 3D obstacle avoidance.
- Write the sensor fusion logic (IMU Gyro/Accel) to compute Pitch/Roll for slope detection.
- Add dynamic Slope Traversal logic (High-Torque/Medium-Speed mode) to `control_proc.py`.

## 3rd Milestone: Evacuation Zone & GUI
- Develop the "Zero-Weight" OpenCV and YOLO11n-seg pipelines for evacuation zone ball detection.
- Benchmark and hot-swap OpenCV vs YOLO on the physical arena.
- Finalize the fully decoupled `gui_proc.py` using CustomTkinter to render real-time telemetry gauges (IMU, Odometry, Line Error) across the separate CPU core.
