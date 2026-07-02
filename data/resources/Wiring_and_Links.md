# Wiring, Pinouts, and External Resources

## Circuit Design Links
- [Main Circuit Design](https://app.cirkitdesigner.com/project/f580b8e3-f0ca-49b9-80c8-28521a5a5665)
- [Alternative Prototype](https://app.cirkitdesigner.com/project/3d586156-ec8d-4c36-8379-9c99c1b2dfc7)
- [Final Prototype Design](https://app.cirkitdesigner.com/project/1892f78e-7115-4b1b-a62e-ec4acb310e49)
- [Project Image Gallery](https://photos.app.goo.gl/16j9BJs6UpAgtNSf6)

## Full Pinout Mapping (ESP32 30-Pin)

### Drive Train (TB6612FNG)
| Motor | Speed (PWM) | Dir 1 | Dir 2 | Standby |
| :--- | :--- | :--- | :--- | :--- |
| **Front Left** | D12 | D27 | D14 | D13 |
| **Front Right** | D21 | D23 | D22 | D15 |
| **Rear Left** | D32 | D35 | D34 | D33 |
| **Rear Right** | D19 | D18 | D5 | D4 |

### Sensors & Indicators
- **1-Wire Data:** D26
- **Red LED:** RX0 (via 200Ω resistor)
- **Green LED:** TX0 (via 200Ω resistor)

## Power Architecture
- **Battery:** 3S LiPo (12.6V Max)
- **Motor Voltage (VMOT):** Fed directly from battery (+V) via 10A Fuse.
- **Logic Voltage (VCC):** 5V derived via LM2596 Buck Converter.
- **Microcontroller Power:** VIN pin connected to the 5V Buck rail.

---
*Generated based on project design documentation and schematics.*
