# Critical Hardware & Safety Review

This document summarizes the safety analysis performed for the DPSI-LFR project.

## 1. Motor Driver Capacity Warnings
- **The Risk:** Driving 4x 12V 200RPM motors in parallel on a single TB6612FNG is hazardous.
- **Analysis:** Stall current for these motors can reach 2.5A each. Parallel wiring on a 2-channel driver means each channel could see 5.0A, far exceeding the 3.2A peak limit.
- **Mitigation:** Use two TB6612FNG drivers or high-current specialized drivers.

## 2. Power Management
- **Voltage Rails:** Ensure the LM2596 Buck converter is tuned to exactly 5.0V before connecting the ESP32.
- **Protection:** A 10A inline fuse is mandatory for 3S LiPo operation to prevent fire in case of a MOSFET short.

## 3. Sensor Grid Scaling
- **Protocol:** The current 1-Wire implementation retrieves 8 bits.
- **Requirement:** Scaling to a 5x4 grid requires clocking out 24 bits (3 bytes) to cover all 20 sensor states.
- **Architecture:** Move away from \`switch-case\` logic toward a Centroid/Weighted Average algorithm for better steering resolution.

## 4. Signal Integrity
- **EMI:** Ceramic capacitors (0.1\u00b5F) are required on all 4 motors to prevent back-EMF spikes from resetting the microcontroller.
- **Logic Levels:** Verify the sensor data line voltage; use a level shifter if the array pulls up to 5V.

---
