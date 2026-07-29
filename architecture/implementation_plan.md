# Goal Description

Rewrite the Temuv2 software architecture to create **Temuv2.5 (Hybrid Overengineering)**. We will adopt the high-performance multi-process shared memory model from the *Overengineering-squared-RoboCup* repository while retaining the advanced RK4 trajectory kinematics and 3D obstacle avoidance from *TemuFollower*. 

The objective is to achieve a 90 FPS line-tracking control loop on the Raspberry Pi 4B by bypassing the Python GIL, utilizing hardware CSI cameras purely for line-following, and offloading heavy 3D/AI processing and low-level control (driving 2x IBT_2 motor drivers) to other dedicated systems like the ESP32.

## User Review Required

> [!IMPORTANT]
> Please review the completely updated and extensively diagrammed architectural documents I generated for you:
> 1. [System Architecture](file:///Users/roopalisingh/.gemini/antigravity/brain/04f6bd6a-2915-4ad7-8cbb-75545ed09f2f/system_architecture.md) - Features hardware topology diagrams, communication sequencing, and power distribution models.
> 2. [Software Architecture](file:///Users/roopalisingh/.gemini/antigravity/brain/04f6bd6a-2915-4ad7-8cbb-75545ed09f2f/software_architecture.md) - Details the 4-process OS layout with IPC shared memory graphs, the state machine flow, and algorithm pipelines.

## Open Questions

> [!NOTE]
> 1. **Evacuation Zone Ball Detection**: In the software architecture, the RealSense now handles Evac Zone ball alignment. I proposed two options for ball alignment: "Zero-Weight" OpenCV Specular Thresholding OR YOLO11-Nano Segmentation. Do you have a preference for which one we should attempt first? OpenCV will be much faster to implement and run, while YOLO11n-seg is more robust to lighting changes.
> 2. **Camera Hardware**: Do you currently have a Raspberry Pi Camera Module (CSI Ribbon) physically available to plug into the RPi 4B, or do we need to order one?

## Proposed Changes

If approved, the execution phase will involve a massive restructuring of the Python codebase into discrete process modules.

### Multiprocessing Framework
#### [NEW] [mp_manager.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/mp_manager.py)
Create a shared memory orchestrator to allocate zero-copy RAM buffers for sharing float arrays (line error, depth distances) between processes.

### Vision Processes
#### [NEW] [line_cam_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/line_cam_proc.py)
Process using `Picamera2` at 448x252. Will extract 4-8 ROIs, compute centroids, and push the line vector to shared memory.
#### [NEW] [realsense_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/realsense_proc.py)
Process managing the Intel RealSense D435. Will run both the ground plane subtraction (Depth) and the Evacuation Zone ball detection logic (RGB).

### Control & Communications
#### [NEW] [control_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/control_proc.py)
The central orchestrator. Reads from shared memory, runs RK4 integration and the Slew limiter, and computes final motor RPMs.
#### [NEW] [serial_io_proc.py](file:///Users/roopalisingh/PycharmProjects/Temuv2/serial_io_proc.py)
Dedicated loop for constructing UART packets (`SOF 0xAA`) and writing to `/dev/ttyUSB0` at 115200+ baud.

## Verification Plan

### Manual Verification
- Launch the multi-process stack on the RPi.
- Verify using `htop` that the Python workload is distributed across all 4 CPU cores.
- Verify that UART motor packets continue streaming smoothly at 60Hz+ even when the RealSense camera lags or blocks.
