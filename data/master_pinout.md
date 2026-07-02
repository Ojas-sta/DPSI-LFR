# DPSI-LFR V2 Master Pinout

This document outlines the pin mappings for the **Raspberry Pi 4B (single-board controller)** and the **ESP32-S3 (alternative production node)**.

---

## 🧠 Node 1: Raspberry Pi 4B & Peripherals

The Raspberry Pi now handles computer vision, direct L298N motor PWM, MPU6050 IMU logging, and competition indicators (LEDs/Buzzer).

### 1. Preserved Legacy UART Pins
These pins are preserved from the older two-node layout. They are not required by the Pi-only controller, but are intentionally not reassigned.
* **TX:** GPIO 14 (Physical Pin 8)
* **RX:** GPIO 15 (Physical Pin 10)
* **GND:** Physical Pin 6

### 2. Competition Indicators (feedback.py)
* **Red LED:** GPIO 5 (Physical Pin 29)
* **Green LED:** GPIO 6 (Physical Pin 31)
* **Buzzer (PWM):** GPIO 13 (Physical Pin 33)

### 3. MPU6050 IMU (I2C)
* **SDA:** GPIO 2 (Physical Pin 3)
* **SCL:** GPIO 3 (Physical Pin 5)
* **VCC:** 3.3V (Physical Pin 1)
* **GND:** GND (Physical Pin 9)

### 4. Direct Pi -> L298N Motor Driver Control
These are the new Pi-only motor pins. They avoid the preserved LED, buzzer, I2C, and legacy UART pins.

| L298N Signal | Raspberry Pi BCM GPIO | Physical Pin | Notes |
| :--- | :---: | :---: | :--- |
| **`ENA`** (Left Motor PWM) | GPIO 12 | Pin 32 | PWM output |
| **`IN1`** (Left Direction A) | GPIO 16 | Pin 36 | Digital output |
| **`IN2`** (Left Direction B) | GPIO 20 | Pin 38 | Digital output |
| **`IN3`** (Right Direction A) | GPIO 21 | Pin 40 | Digital output |
| **`IN4`** (Right Direction B) | GPIO 26 | Pin 37 | Digital output |
| **`ENB`** (Right Motor PWM) | GPIO 18 | Pin 12 | PWM output |
| **`GND`** | Any Pi GND | Pin 6/9/14/20/25/30/34/39 | Must share ground with L298N |

Power notes:
* Do not power the N20 motors from the Pi 5V rail.
* Use the LM2596 buck converter for the logic rail as wired, and a suitable motor supply for the L298N motor input.
* Keep Pi GND, L298N GND, and motor-supply GND common.

### 5. Camera Mounting Recommendation
For the rear-caster chassis (140 mm track width, 180 mm caster arc), start with:
* Camera height: 85-120 mm above the mat.
* Camera pitch: 18-25 degrees downward from horizontal; start at 22 degrees.
* Aim point: bottom third of the image should see roughly 60-90 mm in front of the drive axle.
* Keep the lens centered on the robot centerline and rigidly mounted; tune software ROI before changing pins or wiring.

---

## ⚙️ Node 2 (Alternative): ESP32-S3 (Main Production Node)

*Note: For the full production build utilizing the 10x TCRT5000 IR array.*

### 1. Dual Motor Control (L298N)
| Target Signal | ESP32-S3 Pin |
| :--- | :---: |
| **`ENA`** | GPIO 13 |
| **`IN1`** | GPIO 12 |
| **`IN2`** | GPIO 11 |
| **`IN3`** | GPIO 10 |
| **`IN4`** | GPIO 3 |
| **`ENB`** | GPIO 46 |

### 2. 10-Channel IR Reflectance Array (TCRT5000)
| Sensor Position | Target Signal | ESP32-S3 Pin |
| :--- | :--- | :---: |
| **Far Left** | `IR_1` | GPIO 1 |
| **Left Outer** | `IR_2` | GPIO 2 |
| **Left Mid-Outer**| `IR_3` | GPIO 4 |
| **Left Mid-Inner**| `IR_4` | GPIO 5 |
| **Center Left** | `IR_5` | GPIO 6 |
| **Center Right** | `IR_6` | GPIO 7 |
| **Right Mid-Inner**| `IR_7` | GPIO 15 |
| **Right Mid-Outer**| `IR_8` | GPIO 16 |
| **Right Outer** | `IR_9` | GPIO 17 |
| **Far Right** | `IR_10` | GPIO 18 |

### 3. Communication & Peripheral Buses
| Bus / Peripheral | Target Signal | ESP32-S3 Pin | Note |
| :--- | :--- | :---: | :--- |
| **I2C Data** | `SDA` | GPIO 38 | Shared by OLED & IMU |
| **I2C Clock** | `SCL` | GPIO 39 | Shared by OLED & IMU |
| **UART TX** | `TX` | GPIO 43 | Pi UART RX |
| **UART RX** | `RX` | GPIO 44 | Pi UART TX |

### 4. Indicators
| Indicator | Target Signal | ESP32-S3 Pin |
| :--- | :--- | :---: |
| **Green LED** | `LED_GREEN` | GPIO 41 |
| **Red LED** | `LED_RED` | GPIO 42 |
