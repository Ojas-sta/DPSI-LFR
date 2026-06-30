# DPSI-LFR V2 Master Pinout (ESP32-S3)

Here is the finalized hardware pin mapping for the ESP32-S3. This pinout applies to both your **Main Production Firmware** and your **RC Post Controller (Diagnostic) Firmware**. 

*Note: The motor pins are perfectly grouped sequentially on the left side of the development board for extremely clean wiring.*

## 1. Dual Motor Control (L298N)
| Target Signal | Description | ESP32-S3 Pin |
| :--- | :--- | :---: |
| **`ENA`** | Left Motor Speed (PWM) | **GPIO 13** |
| **`IN1`** | Left Motor Direction A | **GPIO 12** |
| **`IN2`** | Left Motor Direction B | **GPIO 11** |
| **`IN3`** | Right Motor Direction A | **GPIO 10** |
| **`IN4`** | Right Motor Direction B | **GPIO 9** |
| **`ENB`** | Right Motor Speed (PWM) | **GPIO 46** |

## 2. 10-Channel IR Reflectance Array (TCRT5000)
| Sensor Position | Target Signal | ESP32-S3 Pin |
| :--- | :--- | :---: |
| **Far Left** | `IR_1` | **GPIO 1** |
| **Left Outer** | `IR_2` | **GPIO 2** |
| **Left Mid-Outer**| `IR_3` | **GPIO 4** |
| **Left Mid-Inner**| `IR_4` | **GPIO 5** |
| **Center Left** | `IR_5` | **GPIO 6** |
| **Center Right** | `IR_6` | **GPIO 7** |
| **Right Mid-Inner**| `IR_7` | **GPIO 15** |
| **Right Mid-Outer**| `IR_8` | **GPIO 16** |
| **Right Outer** | `IR_9` | **GPIO 17** |
| **Far Right** | `IR_10` | **GPIO 18** |

## 3. Communication & Peripheral Buses
| Bus / Peripheral | Target Signal | ESP32-S3 Pin | Note |
| :--- | :--- | :---: | :--- |
| **I2C Data** | `SDA` | **GPIO 38** | Shared by OLED & IMU |
| **I2C Clock** | `SCL` | **GPIO 39** | Shared by OLED & IMU |
| **Raspberry Pi UART**| `TX` | **GPIO 43** | Pi UART RX (Main firmware only) |
| **Raspberry Pi UART**| `RX` | **GPIO 44** | Pi UART TX (Main firmware only) |

## 4. Rescue Arena Indicator LEDs
*(These are used by the main line-following firmware to indicate Green/Red dot detection)*
| Indicator | Target Signal | ESP32-S3 Pin |
| :--- | :--- | :---: |
| **Green LED** | `LED_GREEN` | **GPIO 41** |
| **Red LED** | `LED_RED` | **GPIO 42** |
