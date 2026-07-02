# In-Depth Guide: 4-Motor Independent Control (Encoder-less)

## 1. System Architecture: The 4-Wheel Drive Advantage
With 4 independent motors, the robot gains superior traction and the ability to execute complex maneuvers like zero-radius turns (pivoting on the spot) and high-torque linear acceleration. Without encoders, the challenge is ensuring that all 4 motors work in a synchronized "Kinematic Harmony" to prevent "Mechanical Fighting" (where wheels on the same side fight each other due to power variance).

## 2. Theoretical Kinematics (The Skid-Steer Model)
Since you are using a 4x5 sensor grid for line following, your primary mode of movement is **Differential Steering**.

### The Quadrant Mapping:
*   **Front Left (FL) & Rear Left (RL)**: Grouped as the "Left Bank."
*   **Front Right (FR) & Rear Right (RR)**: Grouped as the "Right Bank."

### Movement Formulas:
1.  **Forward/Backward**: $V_{FL} = V_{RL} = V_{FR} = V_{RR}$
2.  **Pure Pivot (Zero-Radius)**: $V_{LeftBank} = -V_{RightBank}$
3.  **Proportional Curve**: $V_{LeftBank} = BaseSpeed + SteeringCorrection$ and $V_{RightBank} = BaseSpeed - SteeringCorrection$

## 3. The "Power Balancing" Logic (No-Encoder Synchronization)
Without encoders to check RPM, small differences in motor quality or friction will cause the robot to drift. 

### Logical Solution: The Bias Variable
Introduce a `MotorBias` parameter in your `Movement.py` logic. Since you have 4 independent channels, you can apply a tiny multiplier to individual motors to compensate for hardware drift:
- $FinalPower = TargetPower \times Bias$
- **Calibration**: If the robot drifts left when commanded "Straight," you increase the `Bias` for the Left Bank or decrease it for the Right Bank.

## 4. Vector-Based Steering without Odometry
Your AI Engine provides a **Heading Vector** (calculated via PCA in `AI_Goal.py`). 

### The Control Loop:
1.  **Acquire Vector**: Extract the line angle ($\theta$) from the 4x5 grid.
2.  **Calculate Offset**: Determine how far the line is from the center of the grid ($L_{offset}$).
3.  **Instruction Synthesis**:
    - **Steering Component**: $S = Kp_{angle} \times \theta$
    - **Centering Component**: $C = Kp_{position} \times L_{offset}$
    - **Final Instruction**: $TotalCorrection = S + C$
4.  **Distribution**: 
    - `Left_Motors = Base_Speed + TotalCorrection`
    - `Right_Motors = Base_Speed - TotalCorrection`

## 5. Advanced Maneuver: The "Pivot-Slide"
To handle sharp curves or intersections without encoders:
*   **Step 1**: Identify the shape using `engine.classify(grid)`.
*   **Step 2**: If "Intersection" is detected, enter a **Timed Pulse** phase. 
*   **Step 3**: Because you can't measure distance, you use the **Visual Exit Condition**. The motors continue the maneuver until the AI Engine sees the "Exit Geometry" (e.g., the line becomes a `vertical_line` in the top 2 rows of the 4x5 grid).

## 6. Overcoming Hardware Limitations
*   **Voltage Compensation**: Without encoders, as battery voltage drops, your $Kp$ values might become "sluggish." **Logical Fix**: Normalize your motor outputs based on a voltage read (if available) or use a "Boost Pulse" at the start of every movement to overcome static friction.
*   **Traction Control**: With 4 motors, if one wheel slips, the other three maintain the trajectory. The AI Engine detects the *resulting* error in the line vector and automatically increases power to the correct side to compensate, effectively providing "Visual Traction Control."

## 7. Summary of Instructions for 4 Motors
| Goal | Motor Instructions |
| :--- | :--- |
| **Straight** | All 4 motors at $X\%$ power + Bias correction. |
| **Sharp Right** | Left motors forward, Right motors backward (Pivot). |
| **Slight Veer** | Left motors at $X+10\%$, Right motors at $X-10\%$. |
| **Alignment** | Use PCA vector angle to constantly micro-adjust the ratio between Left and Right banks. |
