# ESP32-S3 High-Performance 4-Motor Wiring Map

## 1. L298N Motor Driver 1 (Motors 1 & 2)
| ESP32-S3 GPIO | L298N Pin | Function |
| :--- | :--- | :--- |
| **1** | ENA | Motor 1 Speed (PWM) |
| **2** | IN1 | Motor 1 Direction A |
| **4** | IN2 | Motor 1 Direction B |
| **5** | ENB | Motor 2 Speed (PWM) |
| **6** | IN3 | Motor 2 Direction A |
| **7** | IN4 | Motor 2 Direction B |

## 2. L298N Motor Driver 2 (Motors 3 & 4)
| ESP32-S3 GPIO | L298N Pin | Function |
| :--- | :--- | :--- |
| **8** | ENA | Motor 3 Speed (PWM) |
| **9** | IN1 | Motor 3 Direction A |
| **10** | IN2 | Motor 3 Direction B |
| **11** | ENB | Motor 4 Speed (PWM) |
| **12** | IN3 | Motor 4 Direction A |
| **13** | IN4 | Motor 4 Direction B |

## 3. Encoder Wiring (Optical/Magnetic)
*Connect Phase A and B from each motor to the following S3 pins:*

| Motor | Phase A (Interrupt) | Phase B (Direction) |
| :--- | :--- | :--- |
| **Motor 1** | **14** | **15** |
| **Motor 2** | **16** | **17** |
| **Motor 3** | **18** | **21** |
| **Motor 4** | **38** | **39** |

## 4. Power & Safety
- **Common Ground**: Ensure ESP32-S3 GND is connected to both L298N GND terminals.
- **Strapping Pin Avoidance**: This configuration avoids GPIO 0, 3, 45, and 46 to ensure reliable booting.
- **Pull-ups**: The firmware uses internal `INPUT_PULLUP` for encoders. If noise is detected, add external 10k resistors.
