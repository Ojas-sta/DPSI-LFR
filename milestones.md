# Project Milestones

## 1st Milestone: Get Robot Moving
- Finalize the laser cutting and physical assembly of the 3-layer chassis.
- Mount the drive motors, casters, and RRC Lite Controller.
- Establish micro-ROS communication between the Raspberry Pi 5 and the STM32.
- Integrate the Tuvaro & RK4 logic to achieve basic, high-speed line following.

## 2nd Milestone: Robotic Arm Moving
- Mount the MeArm v1 to the front of Layer 2.
- Wire the 4 micro-servos to the RRC Lite Controller.
- Validate basic servo control through micro-ROS.
- Implement MoveIt 2 for inverse kinematics and basic pick-and-place trajectories.

## 3rd Milestone: Compare ROS with Traditional Frameworks
- Evaluate the overhead of running ROS 2 Jazzy on the Raspberry Pi 5 versus running bare-metal Python/C++ scripts (like the legacy `TemuFollower` codebase).
- Compare the ease of implementing SLAM and Nav2 in ROS against custom state-machine logic.
- Document the findings to justify the use of ROS 2 for the final competition run.
