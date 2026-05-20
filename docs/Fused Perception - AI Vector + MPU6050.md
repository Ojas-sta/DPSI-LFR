# Fused Perception Logic: AI Vector + MPU6050 Backup

## 1. The Hierarchy of Truth
In this system, the **AI Vector (Visual)** is the Primary Truth, and the **MPU6050 (Inertial)** is the Secondary Backup. 
- **AI Vector**: Used for "Precision Catch" and micro-alignment.
- **MPU6050**: Used for "Blind Pivot" estimation and ensuring the robot doesn't spin infinitely if it loses the line.

## 2. Phase 1: The Blind Pivot (AI-Guided)
When a turn is initiated (e.g., $90^\circ$ right):
- **Motor Instruction**: Start a high-torque pivot using all 4 motors.
- **MPU6050 Role**: Monitor the yaw rate. If the robot has turned $70^\circ$ and the AI hasn't "caught" a line yet, the MPU6050 prevents a runaway spin by slowing down the motors to "Search Speed."
- **AI Role**: Even during the pivot, the AI is scanning. It isn't just looking for "a line"; it's calculating the **Vector of Arrival**.

## 3. Phase 2: The Precision Catch (Main Driver)
This is the "Catch" phase where the AI Vector logic takes full control.
- **Trigger**: The moment the 4x5 grid detects a `vertical_line` or `curve` classification.
- **AI Vector Logic**: 
    - The PCA logic calculates the angle $\theta$ of the incoming line.
    - Instead of a hard stop, the robot performs **Dynamic Braking**.
    - **Instruction**: Power to the motors is proportional to $\theta$. As $\theta \to 0$, motor power is redirected to Forward velocity ($V_y$) and removed from Pivot velocity ($V_{\omega}$).
- **The "Snap"**: The robot "snaps" onto the line because the AI Vector knows exactly when the chassis is parallel to the track geometry.

## 4. Phase 3: Refinement & Correction (The Fusion)
If the robot overshoots due to momentum:
- **Primary Fix (AI)**: The PCA vector will show a negative angle. The 4 motors immediately reverse their differential to pull the vector back to $0^\circ$.
- **Secondary Fix (MPU)**: If the AI is confused by a noisy grid (e.g., a "T" junction), the MPU6050 provides a "Stability Check." If the MPU says the robot is at $95^\circ$ but the AI is seeing a vector that implies $45^\circ$, the system trusts the MPU to continue the turn until the AI sees a vector that makes physical sense ($\approx 90^\circ$).

## 5. 4-Motor Distribution Logic
To execute this fusion, motor power is calculated as:
$$P_{Left} = Base + (K_{AI} \cdot \theta_{AI}) + (K_{MPU} \cdot \Delta Yaw)$$
$$P_{Right} = Base - (K_{AI} \cdot \theta_{AI}) - (K_{MPU} \cdot \Delta Yaw)$$

- **Weighting**: $K_{AI}$ is high (Precision), while $K_{MPU}$ is low (Refinement/Backup).

## 6. Strategic Advantages
1. **Zero Drift**: Even if the MPU6050 drifts by $10^\circ$ during a long run, the AI "Catch" corrects the error every time a line is found.
2. **Speed**: The "Blind Pivot" allows for high-speed rotation, while the "Precision Catch" ensures you don't lose the line at that speed.
3. **Redundancy**: If a sensor in the 4x5 grid fails, the MPU6050 can still complete a "rough" turn based on pure inertia until a valid line vector is regained.
