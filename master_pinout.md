# DPSI-LFR V2 Master Pinout

This document outlines the pin mappings for the **Raspberry Pi 4B (High-Level Brain)**, the **ESP8266 (Diagnostics/Motor Actuation Node)**, and the **ESP32-S3 (Alternative Main Production Node)**.

---

## 🧠 Node 1: Raspberry Pi 4B & Peripherals

The Raspberry Pi handles computer vision, MPU6050 IMU logging, and competition indicators (LEDs/Buzzer).

### 1. Serial Communication (to ESP8266)
*Connect these pins if using Hardware UART instead of a USB Serial cable.*
* **TX:** GPIO 14 (Physical Pin 8) ➔ ESP8266 RX
* **RX:** GPIO 15 (Physical Pin 10) ➔ ESP8266 TX
* **GND:** Physical Pin 6 ➔ ESP8266 GND

### 2. Competition Indicators (feedback.py)
* **Red LED:** GPIO 5 (Physical Pin 29)
* **Green LED:** GPIO 6 (Physical Pin 31)
* **Buzzer (PWM):** GPIO 13 (Physical Pin 33)

### 3. MPU6050 IMU (I2C)
* **SDA:** GPIO 2 (Physical Pin 3)
* **SCL:** GPIO 3 (Physical Pin 5)
* **VCC:** 3.3V (Physical Pin 1)
* **GND:** GND (Physical Pin 9)

---

## 🔌 Node 2: ESP8266 (Diagnostics Node)

The ESP8266 handles manual dashboard control, WebSocket communication, and physical motor driving.

### 1. Motor Driver Control (L298N)
| Signal Name | ESP8266 Pin | Physical NodeMCU Pin |
| :--- | :---: | :---: |
| **`ENA`** (Left Motor PWM) | `D6` | GPIO 12 |
| **`IN1`** (Left Direction A) | `D5` | GPIO 14 |
| **`IN2`** (Left Direction B) | `D4` | GPIO 2 |
| **`IN3`** (Right Direction A) | `D3` | GPIO 0 |
| **`IN4`** (Right Direction B) | `D2` | GPIO 4 |
| **`ENB`** (Right Motor PWM) | `D1` | GPIO 5 |

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
