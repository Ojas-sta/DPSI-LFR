# Software Architecture: Temuv2.5 (Hybrid Overengineering)

This document provides a highly extensive and deeply technical view of the Multi-Process Software Architecture. 

By eliminating Python's Global Interpreter Lock (GIL) through native OS process forking and utilizing zero-copy RAM buffers, we guarantee that Heavy Vision Operations (like RealSense Depth mapping and YOLO11n AI segmentation) will **never** cause the primary steering kinematics (RK4 tracking loop) to drop below 60 FPS.

---

## 1. Multi-Processing OS Layout

The system spans 4 independent Linux processes. The OS kernel's Completely Fair Scheduler (CFS) automatically pins these processes across the Raspberry Pi 4B's four ARM Cortex-A72 physical cores.

```mermaid
graph TB
    subgraph Core_0 [CPU Core 0: High-Speed Line Vision]
        P1(line_cam_proc.py)
        P1_L1[Initialize Picamera2]
        P1_L2[Read 448x252 @ 90FPS]
        P1_L3[Numba @njit HSV Masking]
        P1_L4[Extract 8 ROIs]
        
        P1 --> P1_L1 --> P1_L2 --> P1_L3 --> P1_L4
    end

    subgraph Core_1 [CPU Core 1: Heavy Depth & AI Vision]
        P2(realsense_proc.py)
        P2_L1[Initialize Intel D435 USB]
        P2_L2[Wait For Frames: Depth & RGB]
        P2_L3[10th Percentile Floor Subtraction]
        P2_L4[Evac Zone: OpenCV Specular / YOLO]
        
        P2 --> P2_L1 --> P2_L2 --> P2_L3 --> P2_L4
    end

    subgraph Zero_Copy_IPC [RAM: multiprocessing.shared_memory]
        SHM1[(Line Error Vector Buffer)]
        SHM2[(Depth Obstacle Buffer)]
        SHM3[(Evac Ball Target Buffer)]
        SHM4[(Motor Target RPM Buffer)]
    end

    subgraph Core_2 [CPU Core 2: Kinematic Orchestrator]
        P3(control_proc.py)
        P3_L1[Read SHM Blocks Instantly]
        P3_L2[State Machine: Track vs Evac vs Stop]
        P3_L3[Runge-Kutta 4th Order Math]
        P3_L4[Slew Limiter Filter]
        
        P3 --> P3_L1 --> P3_L2 --> P3_L3 --> P3_L4
    end

    subgraph Core_3 [CPU Core 3: Serial I/O]
        P4(serial_io_proc.py)
        P4_L1[Read Target RPM Buffer]
        P4_L2[Build Binary Packet]
        P4_L3[Write to /dev/ttyUSB0 @ 115200]
        
        P4 --> P4_L1 --> P4_L2 --> P4_L3
    end

    %% IPC Links
    P1_L4 ==|Write (0.01ms)|==> SHM1
    P2_L3 ==|Write (0.01ms)|==> SHM2
    P2_L4 ==|Write (0.01ms)|==> SHM3
    
    SHM1 ==|Read|==> P3_L1
    SHM2 ==|Read|==> P3_L1
    SHM3 ==|Read|==> P3_L1
    
    P3_L4 ==|Write|==> SHM4
    SHM4 ==|Read|==> P4_L1
```

---

## 2. Algorithm Pipelines

### 2.1 The Ultra-Fast Line Tracking Pipeline (`line_cam_proc.py`)
> **Source**: Raspberry Pi Camera Module (CSI). **Framerate**: 90 FPS.

Because the Pi Camera uses the hardware ISP and completely bypasses the USB controller, we dedicate it *solely* to tracking the line.
1. **Acquisition**: `Picamera2` grabs frames downsampled to exactly `448 x 252` pixels.
2. **JIT Acceleration**: Image arrays are passed to a function decorated with `Numba @njit(fastmath=True)`. Python's slow internal iteration is completely replaced by compiled C-level machine code.
3. **HSV Masking**: The array is masked to isolate the black line and the green intersection markers.
4. **ROI Slicing (4-8 Blocks)**: The image is divided horizontally into 4 to 8 slices (Regions of Interest).
5. **Centroid Mathematics**: The center of mass for the line segment in each ROI is calculated. A curve vector is generated and written into the `multiprocessing.shared_memory` buffer for the Control Process.

### 2.2 The Heavy Depth & AI Pipeline (`realsense_proc.py`)
> **Source**: Intel RealSense D435 (USB 3.0). **Framerate**: 30 FPS.

This process handles computationally heavy tasks. It runs at a lower framerate (30 FPS), but because it is in a separate OS process, it **never slows down the 90 FPS steering**.

**A. Trajectory Safety (Depth Stream)**:
1. `wait_for_frames()` blocks until a new 640x480 Depth Z16 frame arrives over USB.
2. We mathematically project where the "flat floor" should be based on camera pitch and mounting height.
3. We subtract the actual depth from the "expected floor". Any pixels remaining represent vertical physical objects.
4. We take the **10th percentile closest value** to filter out sensor noise and determine exactly how close the nearest physical obstacle is.
5. We write this safety distance float to shared memory.

**B. Evacuation Zone Ball Alignment (RGB Stream)**:
*Note: This logic only executes when the State Machine enters the Evac Zone state.*
1. **Option 1 (Zero-Weight Absolute Lightest)**: Pure OpenCV Specular / Thresholding Pipeline. Looks for the high-intensity specular highlight of the silver balls, combined with Hough Circles or shape contour circularity metrics.
2. **Option 2 (YOLO11n-seg)**: We run a lightweight YOLO11-Nano semantic segmentation model. It draws bounding boxes and masks around "Dead Victim (Black)" and "Alive Victim (Silver)".
3. We calculate the X-offset of the target ball from the center of the frame and write an "Alignment Error Vector" to shared memory.

### 2.3 The Control & Kinematics Orchestrator (`control_proc.py`)
This is the logical brain of the robot.

```mermaid
stateDiagram-v2
    [*] --> LineFollowing
    
    state LineFollowing {
        Read_Shared_Error --> Calculate_RK4
        Calculate_RK4 --> Apply_Slew_Limiter
        Apply_Slew_Limiter --> Set_Target_RPM
    }
    
    LineFollowing --> ObstacleAvoidance : Depth < 15cm
    ObstacleAvoidance --> LineFollowing : Depth > 20cm
    
    LineFollowing --> EvacuationZone : Silver Strip Detected
    
    state EvacuationZone {
        ScanForBalls --> AlignToBall
        AlignToBall --> CaptureSequence
        CaptureSequence --> DepositSequence
    }
    
    EvacuationZone --> LineFollowing : Exit Marker Found
```

1. **State Machine Execution**: Instantly reads the Line Vector, Obstacle Distance, and Ball Alignment from shared memory.
2. **RK4 Numerical Integration**: Instead of simple Proportional steering, we use Runge-Kutta 4th Order math to mathematically predict the robot's smooth arc toward the line centroid over the `dt` timestep.
3. **Slew Limiter**: A recursive filter algorithm restricts the maximum mathematical rate of change (acceleration) sent to the motors. This ensures the tires never lose static friction (slip) when the RK4 loop requests a sudden sharp turn on a 90-degree intersection.
