# DPSI-LFR V2 Master Pinout

This document outlines the pin mappings for the **Raspberry Pi 4B (High-Level Brain)**, the **Arduino Uno (Serial Diagnostics/Motor Actuation Node)**, and the **ESP32-S3 (Alternative Main Production Node)**.

---

## 🧠 Node 1: Raspberry Pi 4B & Peripherals

The Raspberry Pi handles computer vision, MPU6050 IMU logging, and competition indicators (LEDs/Buzzer).

### 1. Serial Communication (to Arduino Uno)
*Connect these pins if using Hardware UART instead of a USB Serial cable.*
* **TX:** GPIO 14 (Physical Pin 8) -> Arduino Uno RX (`D0`)
* **RX:** GPIO 15 (Physical Pin 10) <- Arduino Uno TX (`D1`) through a 5V-to-3.3V level shifter or divider
* **GND:** Physical Pin 6 -> Arduino Uno GND

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

## 🔌 Node 2: Arduino Uno (Serial Diagnostics Node)

The Arduino Uno handles serial diagnostics commands and physical motor driving. The old ESP8266 Wi-Fi dashboard and WebSocket functions have been removed.

### 1. Motor Driver Control (L298N)
| Signal Name | Arduino Uno Pin | Notes |
| :--- | :---: | :--- |
| **`ENA`** (Left Motor PWM) | `D5` | PWM |
| **`IN1`** (Left Direction A) | `D7` | Digital output |
| **`IN2`** (Left Direction B) | `D8` | Digital output |
| **`IN3`** (Right Direction A) | `D9` | Digital output |
| **`IN4`** (Right Direction B) | `D10` | Digital output |
| **`ENB`** (Right Motor PWM) | `D6` | PWM |

### 2. ESP8266-to-Uno Migration Map
| L298N Signal | Old ESP8266 Pin | Old ESP GPIO | New Arduino Uno Pin |
| :--- | :---: | :---: | :---: |
| **`ENA`** (Left PWM) | `D6` | GPIO 12 | `D5` PWM |
| **`IN1`** | `D5` | GPIO 14 | `D7` |
| **`IN2`** | `D4` | GPIO 2 | `D8` |
| **`IN3`** | `D3` | GPIO 0 | `D9` |
| **`IN4`** | `D2` | GPIO 4 | `D10` |
| **`ENB`** (Right PWM) | `D1` | GPIO 5 | `D6` PWM |

### 3. Serial Command Protocol
| Command | Meaning |
| :--- | :--- |
| `M:<left>,<right>` | Set motor speeds in `-1.0..1.0` when armed and in auto mode |
| `A:<0|1>` | Disarm or arm the motor output |
| `C:<0|1>` | Set manual mode (`0`) or auto serial-control mode (`1`) |
| `P` | Ping; Uno replies with `P_ACK` |
| `T:<ms>,<left>,<right>,<watchdog>,<armed>,<auto>` | Periodic serial telemetry from Uno |

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
