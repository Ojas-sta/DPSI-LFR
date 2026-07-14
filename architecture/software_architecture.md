# Software Architecture

The software architecture is built entirely on **ROS 2 Jazzy** to ensure modularity and scalability.

## 1. High-Speed Line Following Mode
- **Vision Processing**: The Downward Pi Camera feeds into a 3-ROI extractor (Left, Center, Right). 
- **Control Logic (Tuvaro & RK4)**: Imported from the `TemuFollower` logic, a highly optimized adaptive PID (or RK4 solver) takes the ROI errors and outputs high-speed steering commands.
- **Behavior**: The robot tracks the line at high speed while scanning for Red/Green marker dots and handling gaps/intersections.

## 2. Autonomous Navigation Mode
Once the robot enters the separate sorting room, the line tracking terminates.
- **SLAM & Mapping**: The SLAM Toolbox constructs a 2D occupancy grid of the room using the Intel RealSense depth data.
- **Localization (EKF)**: An Extended Kalman Filter fuses the wheel encoder odometry, IMU data, and RealSense visual odometry to maintain a highly accurate pose estimate.
- **Path Planning**: Nav2 handles global and local planning, routing the robot around the unlined room to search for the pucks and target bins.

## 3. Manipulation Mode
- **Kinematics**: MoveIt 2 manages the inverse kinematics and collision-free trajectory planning for the MeArm v1.
- **Computer Vision**: The Arm Pi Camera runs color/object detection to identify black/white pucks and red/green bins.
- **Execution**: MoveIt 2 sends joint trajectories to a custom micro-ROS arm controller on the STM32, which drives the 4 servos to grasp and sort the pucks.

## High-Level Orchestration
- **Behavior Trees (BT)**: A central BT orchestrates the state transitions:
  `Line Following` -> `Room Entry` -> `Search for Pucks` -> `Grasp Puck` -> `Search for Bin` -> `Drop Puck`.
