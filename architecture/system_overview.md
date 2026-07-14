# System Overview

The DPSI LFR V3 is designed as a hybrid autonomous mobile manipulator. It bridges the gap between high-speed line following robotics and complex spatial navigation and manipulation.

## Core Objectives
1. **High-Speed Line Following**: Navigate a complex track with intersections, gaps, and markers autonomously and rapidly.
2. **Untethered Navigation**: Break away from line-tracking to autonomously map and navigate an unlined room using SLAM and visual odometry.
3. **Complex Manipulation**: Utilize a 4-DOF MeArm v1 to identify, grasp, and sort black and white pucks into designated red and green target bins.

## Hardware Stack Summary
- **Chassis**: Custom 3-layer 17x20 cm laser-cut differential drive chassis.
- **Compute**: Raspberry Pi 5 + RRC Lite Controller (STM32).
- **Vision**: Intel RealSense + 2x Pi Cameras (Downward & Arm-mounted).

## Software Stack Summary
- **OS & Framework**: Ubuntu + ROS 2 Jazzy.
- **Control**: micro-ROS (STM32), Tuvaro & RK4 logic for high-speed tracking.
- **Navigation & Manipulation**: SLAM Toolbox, Nav2, MoveIt 2.
