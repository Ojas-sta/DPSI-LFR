# Hardware Components

## Compute & Processing
- **Raspberry Pi 5**: The main high-level compute unit running Ubuntu, ROS 2 Jazzy, MoveIt 2, and Nav2.
- **RRC Lite Controller**: Features a built-in STM32 chip. It handles real-time low-level control, interfacing directly with the Raspberry Pi 5 via USB (micro-ROS).

## Sensors
- **Intel RealSense Depth Camera**: Mounted forward-facing on the top rear deck (Layer 3). Responsible for SLAM, visual odometry, and obstacle detection.
- **Downward Pi Camera V1.3**: Mounted on Layer 1 facing downwards to track the competition line and detect junctions.
- **Arm Pi Camera**: Mounted on the MeArm v1. Used to detect puck colors (black/white) and target bins (red/green) in the sorting room.
- **IMU**: Integrated into the RRC Lite Controller for odometry and pose estimation.

## Actuation & Mobility
- **Drive Motors**: 2x DC motors with high-resolution encoders connected to the 4-channel encoder ports on the RRC Lite.
- **Robotic Arm**: MeArm v1, powered by 4 standard micro-servos connected directly to the RRC Lite servo ports.
- **Casters**: 2x Ball casters (front and rear) for omnidirectional low-friction support.

## Indicators (Competition Specific)
- **Green LED**: Blinks when a green dot marker is detected on the line.
- **Red LED**: Blinks when a red dot marker is detected, accompanied by a full stop.
