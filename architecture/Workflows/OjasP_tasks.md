# OjasP's Software & Architecture Workflow (July 30th)

> [!IMPORTANT]
> **Operational Directives**
> - You are the lead for the **Temuv2.5 (Hybrid Overengineering)** software architecture.
> - Orchestrate Vatsal's tasks and verify his hardware placements.
> - **STRICT INSTRUCTION**: Do **NOT** work on normal SLAM implementation right now. Focus purely on the high-speed pipeline and the evacuation zone mapping (if required).
> - You are responsible for all soldering (assist Vatsal as needed).
> - Keep all 3 teachers (Danna Ma'am, Shubham Sir, and Shashank Sir) updated on your progress.
> - Utilize **Generative AI** throughout your coding sessions to optimize your workflows and debug faster.

---

## Task 1: Environment Setup & Git Version Control
- [ ] **Action**: Set up the Python virtual environment (`venv`) on the Raspberry Pi 4B.
- [ ] **Details**: Ensure all dependencies (`numba`, `picamera2`, `opencv-python`, `pyrealsense2`, `customtkinter`) are installed inside the isolated environment.
- [ ] **Verification**: Enforce proper Git version control. Use the `dpsi_lfr_v3` branch, create Pull Requests for major features, and document all commits clearly.

## Task 2: Implement High-Speed Line Following
- [ ] **Action**: Write the core logic for the 90 FPS line tracking.
- [ ] **Details**: Integrate the Pi Camera V3 using hardware ISP. Process the HSV masking to isolate the line and write the Error Vector into the `multiprocessing.shared_memory` (Zero-Copy IPC).
- [ ] **Verification**: Tune the PID / RK4 parameters to achieve smooth, jitter-free high-speed tracking.

## Task 3: Implement Green Marker 90-Degree Turns
- [ ] **Action**: Code the logic to detect green intersection markers.
- [ ] **Details**: The Pi Camera's HSV mask must identify green patches on the left/right of the line to trigger strict 90-degree rotational kinematics in the `control_proc.py` state machine.
- [ ] **Verification**: Test the turn execution delay and ensure the robot re-acquires the line instantly after turning.

## Task 4: RealSense IMU Integration
- [ ] **Action**: Bring the Intel RealSense D435i online.
- [ ] **Details**: Write the pipeline in `realsense_proc.py` to extract Gyroscope and Accelerometer data. Apply sensor fusion to calculate Pitch and Roll.
- [ ] **Verification**: Ensure the Pitch metric successfully detects when the robot hits the 30-degree ramp, automatically triggering the High-Torque Medium-Speed traversal state.

## Task 5: Evacuation Zone Implementation
- [ ] **Action**: Program the logic for the Evacuation Zone.
- [ ] **Details**: 
  - Wire the servos for the custom evacuation mechanism that Vatsal is building.
  - If required, implement localized Evacuation Zone mapping (e.g., A* or coordinate arrays) to track silver/black balls. **DO NOT use full-scale 2D SLAM.**
- [ ] **Verification**: Ensure the robot can transition smoothly from line-following to the Evacuation state machine.

## Task 6: CustomTkinter GUI & Telemetry
- [ ] **Action**: Build the `gui_proc.py` monitoring dashboard.
- [ ] **Details**: Create a modern CustomTkinter interface that reads from the `multiprocessing.shared_memory` to render live metrics, odometry graphs, and camera feeds.
- [ ] **Verification**: Ensure the GUI runs in its own process and does not bottleneck the 90 FPS control loop. Document all live metrics visible on the dash.

## Task 7: Solder & Hardware Assistance
- [ ] **Action**: Assist Vatsal with electrical connections.
- [ ] **Details**: Solder the Big Green LED, Big Red LED, Buzzer, XL4016 buck converter, and servo connections.
- [ ] **Verification**: Verify continuity with a multimeter before powering the ESP32 and RPi. Ensure Vatsal places the LED light strip in an optimal location relative to the Pi Camera to prevent glare.

## Task 8: Architecture Integrity & Rule Verification
- [ ] **Action**: Audit the entire system against competition standards.
- [ ] **Details**: Verify the integrity of the Temuv2.5 architecture and your codebase against the RoboCup Junior Rescue Line rules and official annexures.
- [ ] **Verification**: Compare robot performance with official rulebook metrics and reference videos of other successful robots. Document everything.

---
*Note: Print this checklist out if you prefer a physical sheet to track your progress throughout the lab session.*
