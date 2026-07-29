# Vatsal's Hardware & Operations Workflow (July 30th)

> [!IMPORTANT]
> **Operational Chain of Command**
> - You must operate with strict approval from **OjasP** at all times.
> - For any **drastic changes**, you must also receive explicit approval from **Shubham Sir**.
> - Keep all 3 teachers (Danna Ma'am, Shubham Sir, and Shashank Sir) updated on your progress throughout the day.
> - All soldering must be done by **OjasP** or a teacher. Do not solder independently.
> - Document All Tasks

---

## Task 1: Procure the XL4016 Buck Converter
- [ ] **Action**: Call or text the supplier at **+91 09818893668**.
- [ ] **Details**: You need to acquire the XL4016 Buck Converter. Before finalizing the order, **coordinate strictly with OjasP and Shubham Sir** to ensure you are requesting the exact version and specifications required for the robot's power distribution.
- [ ] **Verification**: Confirm with OjasP that the part ordered is the correct 8A/9A 300W version suitable for our servos.

## Task 2: Procure Pi Camera and Cable from Sujoy
- [ ] **Action**: Contact Sujoy at **+91 9891195730**.
- [ ] **Details**: Request the Raspberry Pi Camera along with its CSI ribbon cable. When speaking to him, state that you are calling on behalf of **Ojas_Singh** (make sure to clarify this is different from OjasP).
- [ ] **Verification**: Visually inspect the CSI cable for any kinks or tears upon receipt.

## Task 3: Refine Camera Placement & Mount the Pi Cam
- [ ] **Action**: Mount the Pi Camera on the robot chassis.
- [ ] **Details**: Use the old camera mount (currently kept on the windowsill on the side of the main entrance of the Maker's Space lab). 
- [ ] **Positioning**: Mount it on the underside of the chassis, facing slightly forward. 
- [ ] **Verification**: **CRITICAL**: You must confirm the exact downward/forward angle with **OjasP** before locking down the screws, as this directly affects the line-tracking HSV matrix calibration.

## Task 4: Design and Build the Evacuation Zone Mechanism
- [ ] **Action**: CAD, 3D Print, and construct the Evacuation Zone claw, servos, and storage compartment.
- [ ] **Details**: Since this is a custom design, Make **Shubham Sir**focus on the CAD modeling of a mechanism capable of grabbing the RoboCup rescue balls and storing them safely. 
- [ ] **Verification**: Coordinate with **Shubham Sir** regarding the physical mounting of the mechanism onto the chassis. Ensure the weight distribution doesn't imbalance the differential drive.

## Task 5: Finalize LED and Buzzer Wiring Logic
- [ ] **Action**: Plan the mounting and wiring layout for the Big Green LED, Big Red LED, and the Buzzer.
- [ ] **Details**: Determine exactly where these indicators will sit on the chassis for maximum visibility during a run.
- [ ] **Verification**: **Strictly coordinate with OjasP** for the wiring paths and GPIO/PWM pin assignments on the ESP32. Remember: OjasP or a teacher will do the actual soldering.

## Task 6: Fabricate Obstacles and Rescue Balls
- [ ] **Action**: Create the physical field elements for testing.
- [ ] **Details**: Make orange obstacles (ensure dimensions match standard RoboCup specs) and the rescue balls (Silver for alive victims, Black for dead victims). 
- [ ] **Verification**: Refer directly to the official **RoboCup Junior Rescue Line rules** for the exact dimensions, weights, and color codes of these objects.

## Task 7: Modify the Arena & Integrate the Ramp
- [ ] **Action**: Adjust the physical testing arena to accommodate our robot's footprint and the new architecture.
- [ ] **Details**: 
  - Add **white tiles** along the edges of the arena so the camera does not accidentally see the background floor.
  - Incorporate the **Ramp** into the arena circuit.
- [ ] **Verification**: Ensure the ramp incline does not exceed **30 degrees** maximum, as per the design constraints.

## Task 8: Review Arena Rules & Annexures
- [ ] **Action**: Cross-reference the arena layout against the rulebook.
- [ ] **Details**: Review the official RoboCup Jr rules and any relevant annexures to ensure our test arena accurately simulates competition conditions.
- [ ] **Verification**: Check minimum tile sizes, wall heights, and line widths.

## Task 9: Design Green Marker 90-Degree Turn Paths
- [ ] **Action**: Create specific track segments to test the robot's ability to read green markers.
- [ ] **Details**: Tape down standard black lines with green intersection markers indicating sharp 90-degree left and right turns.
- [ ] **Verification**: Test the reflectivity of the green markers to ensure the Pi Camera can distinguish them from the black line and white floor.

---
*Note: Print this checklist out if you prefer a physical sheet to track your progress throughout the lab session.*
