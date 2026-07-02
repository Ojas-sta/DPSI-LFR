# Gemini Session Log - May 20, 2026

## Session Overview
- **Primary Objective**: Synchronize and commit advanced line-following AI logic from `PythonProject` to the main `DPSI-LFR` repository.
- **Repository**: [DPSI-LFR](https://github.com/Ojas-sta/DPSI-LFR.git)
- **Status**: Successfully updated `src/AI_Goal.py` and added `src/Movement.py`. Changes pushed to remote.

## GEMINI.md Baseline
The project uses a standard `GEMINI.md` for team-shared instructions. Currently, it serves as a placeholder for:
- **Architecture**: (TBD)
- **Conventions**: (TBD)
- **Workflows**: (TBD)

## Technical Analysis of Code (2026-05-20)

### 1. AI_Goal.py: Hybrid Perception Engine
This module implements a sophisticated 4x5 sensor grid analysis tool using two primary methods:

- **Trainable CNN (`TrainableGridCNN`)**:
    - **Architecture**: Single convolution layer (8 filters, 2x2 kernel) followed by ReLU and a Dense layer.
    - **Classification**: Maps 4x5 binary grids into 7 categories (Empty, Point, Horizontal, Vertical, Diagonal, Intersection, Curve).
    - **Learning**: Uses backpropagation with Softmax cross-entropy loss.
- **Parametric Topology Engine (`ParametricGridEngine`)**:
    - **Fallback Logic**: If the CNN is untrained or uncertain, it uses connected component analysis (BFS/DFS) and degree analysis.
    - **Intersection Detection**: Identified by nodes with $\ge 3$ neighbors.
    - **Vector Extraction**: Uses PCA-like logic (covariance matrix) to calculate line endpoints and direction vectors.

### 2. Movement.py: Decision Logic
- **Sensor Mapping**: Converts raw numerical sensor data into boolean matrices for the AI Engine.
- **Case Analysis**: Maps AI classifications to "Cases" (e.g., `vertical_line` $\rightarrow$ `case1`, `intersection` $\rightarrow$ `case4`).
- **Control Theory**: Designed to translate spatial awareness into discrete movement commands.

## Strategic Rationale
The choice of a **Hybrid Perception Engine** (CNN + Topology) is strategic for robotics:
1. **Robustness**: The topological analyzer provides a deterministic ground truth for simple shapes.
2. **Adaptability**: The CNN allows the system to learn complex or noisy patterns that are hard to define parametrically.
3. **Efficiency**: The 4x5 grid is small enough for near-instant inference on low-power hardware.

## Fundamental Logic: Encoder-less Orientation Control

### 1. The "Visual Compass" Concept
Without encoders, the robot lacks internal state awareness (odometry). Instead, it must rely on **External Closed-Loop Feedback**. The 4x5 sensor grid, processed by the PCA-based vector extraction in `AI_Goal.py`, acts as a real-time compass.

### 2. Angular Extraction
The robot's forward axis is defined as $0^\circ$. By applying the arctangent function to the $\Delta X$ and $\Delta Y$ of the principal vector extracted from the grid, the robot calculates its **Relative Heading Error** to the line.

### 3. Instruction Generation (Proportional Control)
The "Instruction" is not a fixed command but a dynamic correction.
- **Steering Correction** = $Kp \times (\text{Target Angle} - \text{Calculated Vector Angle})$.
- As the robot turns, the line "rotates" within the sensor's field of view. When the line aligns with the robot's center axis ($0^\circ$), the correction naturally drops to zero.

### 4. State-Based "Seek and Catch"
For discrete turns (e.g., $90^\circ$ at an intersection):
- **Pivot**: Initiate a spin.
- **Scan**: Continuously run classification logic while spinning.
- **Catch**: Stop the pivot the instant the AI Engine detects a new valid line path (`vertical_line` or `curve`) that aligns with the target orientation.
- **Strategic Benefit**: This method is immune to wheel slip and battery fluctuations that typically cause encoder-based systems to fail.

## Actions Executed
- Verified repository status in `DPSI-LFR`.
- Migrated `AI_Goal.py` and `Movement.py` from `PycharmProjects/PythonProject/`.
- Committed and pushed updates to `main` branch.
- Documented Theoretical Encoder-less Orientation Control strategy.
