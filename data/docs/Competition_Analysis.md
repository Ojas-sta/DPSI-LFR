# Competition Analysis: Rescue Robotics Arena vs. standard RoboCup

This document outlines the critical strategic and technical differences between the local Rescue Robotics Arena competition and the international RoboCup Junior standards.

## Key Technical Challenges

### 1. Surface Reflectivity and Calibration
Standard RoboCup tiles are typically matte. This competition allows Sunmica and whiteboards, which are highly reflective.
**Impact:** IR sensors will likely experience more "noise" from overhead lighting. Calibration logic must be robust.

### 2. Marker Logic Discrepancies
Standard RoboCup use Green Squares to dictate turns. This competition uses "Green Dots" for blink-and-continue tasks. 
**Impact:** A standard RoboCup intersection algorithm will fail here if it treats dots as turn markers.

### 3. Gap and Ramp Parameters
Undefined ramp angles and gap lengths pose a torque and dead-reckoning risk.
**Impact:** The 200RPM motors must be geared appropriately, and software must support a "blind driving" state for gaps.

## Critical Ambiguities (Development Risks)
1. **Marker Placement:** Position relative to the line (on vs. beside).
2. **Rescue Task:** Physical manipulation vs. purely sensor-based detection.
3. **Obstacle Clearance:** Minimum bypass width.

## Strategic Checklist for July 6th Reveal
- [ ] Sample "White" and "Black" values immediately on track reveal.
- [ ] Test "Blink" visibility on the remote camera feed.
- [ ] Verify PID tuning on the specific Sunmica/Whiteboard friction.

---
© 2026 DPSI Rescue Robotics Team.
