# 🔌 TEMUv2.5 COMPLETE HARDWARE SPECIFICATIONS & PINOUT MAP

This document provides the authoritative hardware wiring, power distribution, and GPIO pinout table for **TEMUv2.5**.

---

## 1. Master GPIO Pinout Table (Raspberry Pi 4B)

| Function / Component | GPIO Number | Physical Pin Number | Hardware Signal Type |
| :--- | :---: | :---: | :--- |
| **Servo 1 (Claw)** | `GPIO 17` | **Pin 11** | `gpiozero` DMA Soft-PWM (50Hz) |
| **Servo 2 (Lift)** | `GPIO 27` | **Pin 13** | `gpiozero` DMA Soft-PWM (50Hz) |
| **Servo 3 (Gate)** | `GPIO 22` | **Pin 15** | `gpiozero` DMA Soft-PWM (50Hz) |
| **Servo 4 (Cam Pitch)** | `GPIO 23` | **Pin 16** | `gpiozero` DMA Soft-PWM (50Hz) |
| **MaixCAM Telemetry TX**| `GPIO 14` | **Pin 8** | Hardware UART TX (`/dev/ttyS0`) |
| **MaixCAM Telemetry RX**| `GPIO 15` | **Pin 10**| Hardware UART RX (`/dev/ttyS0`) |
| **Big Green LED** | `GPIO 16` | **Pin 36** | Digital Output (HIGH = ON) |
| **Big Red LED** | `GPIO 26` | **Pin 37** | Digital Output (HIGH = ON) |
| **Active Piezo Buzzer** | `GPIO 12` | **Pin 32** | Digital Output / Tone |
| **Front Ultrasonic TRIG**| `GPIO 20` | **Pin 38** | Digital Output (10µs pulse) |
| **Front Ultrasonic ECHO**| `GPIO 21` | **Pin 40** | Digital Input |
| **Left Ultrasonic TRIG** | `GPIO 5`  | **Pin 29** | Digital Output (10µs pulse) |
| **Left Ultrasonic ECHO** | `GPIO 6`  | **Pin 31** | Digital Input |
| **Right Ultrasonic TRIG**| `GPIO 25` | **Pin 22** | Digital Output (10µs pulse) |
| **Right Ultrasonic ECHO**| `GPIO 24` | **Pin 18** | Digital Input |
| **IBT_2 Motor 1 PWM L** | `GPIO 18` | **Pin 12** | Motor PWM Left |
| **IBT_2 Motor 1 PWM R** | `GPIO 19` | **Pin 35** | Motor PWM Right |
| **IBT_2 Motor 2 PWM L** | `GPIO 13` | **Pin 33** | Motor PWM Left |
| **IBT_2 Motor 2 PWM R** | `GPIO 4`  | **Pin 7**  | Motor PWM Right |
| **System Ground (GND)** | `GND`     | **Pins 9, 14, 20, 25, 30, 34, 39** | Tied to Common Power Ground |

---

## 2. Sensor & Camera Subsystem

1. **Downward PiCamera (CSI):** Dedicated CSI ribbon cable connection directly to Raspberry Pi 4B camera port.
2. **MaixCAM Pro (Edge AI + IMU):** Connected via **Hardware UART Serial (`/dev/ttyS0` / GPIO 14 & 15)** running at 115200 baud.
3. **Ultrasonic Sensor Array (3x HC-SR04):**
   - Front Sensor: GPIO 20 (TRIG) / GPIO 21 (ECHO)
   - Left Sensor: GPIO 5 (TRIG) / GPIO 6 (ECHO)
   - Right Sensor: GPIO 25 (TRIG) / GPIO 24 (ECHO)
4. **Camera Illumination:** Constant-on 12V COB White LED Strip mounted underneath the chassis, powered directly from the regulated 12V motor rail.

---

## 3. Actuators, Drive Train & Wheels

1. **Motor Drivers:** 2x IBT_2 43A High Current Drivers driving 4x 12V DC Geared Motors in a 4WD Skid-Steer / Tank Drive configuration.
2. **Wheels:** **4x Custom High-Traction Neoprene Discs on Aluminum Hubs**.
   - *Design Choice:* Omniwheels are **strictly excluded** due to sideways slipping on 25° competition ramps and speed bumps.
3. **Servos (5 Total):**
   - 4x Metal-Gear Servos (Claw, Lift, Gate, Cam) on **GPIO 17, 27, 22, 23** controlled via `gpiozero` DMA Soft-PWM.
   - 1x Sorting Servo connected directly to and controlled by the MaixCAM Pro NPU.

---

## 4. Power & Voltage Regulation Architecture

```
                    +--------------------------------+
                    |  3-Cell LiPo Battery (11.1V)   |
                    |   (With 10.4V Voltage Alarm)   |
                    +---------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
  [ XL4016 Buck (6.0V) ]    [ 5.2V RPi Regulator ]   [ Regulated 12V Rail ]
            |                       |                       |
            v                       v                       v
  [ 4x Servo Array ]        [ Raspberry Pi 4B ]     [ 2x IBT_2 Drivers ]
                                                    [ 12V COB White LEDs ]
```

---

## 5. Control & Execution Interface

- **Program Control:** Terminal-based execution (`python3 main.py` or SSH terminal start/stop commands inside the Docker container).
- **Indicators:**
  - Big Green LED (GPIO 16) for active line-following status.
  - Big Red LED (GPIO 26) for error / obstacle / stop status.
  - Active Piezo Buzzer (GPIO 12) for audible state change prompts and low-voltage alerts.
