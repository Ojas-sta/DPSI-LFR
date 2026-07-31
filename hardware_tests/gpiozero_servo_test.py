#!/usr/bin/env python3
"""
Modern Pi OS DMA Soft-PWM Servo Test (using built-in gpiozero)
Controls 4 Servos on GPIO 17, 27, 22, 23 (No daemon or PCA required!)

Pinout Assignment:
  - Servo 1: GPIO 17 (Physical Pin 11)
  - Servo 2: GPIO 27 (Physical Pin 13)
  - Servo 3: GPIO 22 (Physical Pin 15)
  - Servo 4: GPIO 23 (Physical Pin 16)
  - Ground:  Tied to Raspberry Pi GND (Pin 9, 14, 20, 25, 30, 34, 39)
  - Power:   External 5V/6V Power Supply (DO NOT power 4 servos from RPi 5V header)
"""

import time
from gpiozero import Servo

# Define min and max pulse widths (500us to 2500us for 0° to 180°)
MIN_PW = 0.0005  # 500 microseconds (0°)
MAX_PW = 0.0025  # 2500 microseconds (180°)

# Initialize Servos on requested General Purpose GPIO pins
PINS = [17, 27, 22, 23]
servos = []

print("==================================================")
print("   GPIOZERO DMA 4-SERVO CONTROL TEST")
print("==================================================")

for p in PINS:
    print(f"[INIT] Configuring Servo on GPIO {p} (DMA Soft-PWM)...")
    s = Servo(p, min_pulse_width=MIN_PW, max_pulse_width=MAX_PW)
    servos.append(s)

print("\n[SUCCESS] All 4 Servos Initialized!")

try:
    while True:
        print("\n>>> Setting All Servos to 0° (MIN)...")
        for i, s in enumerate(servos):
            s.min()
            print(f"  -> Servo on GPIO {PINS[i]} = 0°")
        time.sleep(2.0)

        print("\n>>> Setting All Servos to 90° (CENTER)...")
        for i, s in enumerate(servos):
            s.mid()
            print(f"  -> Servo on GPIO {PINS[i]} = 90°")
        time.sleep(2.0)

        print("\n>>> Setting All Servos to 180° (MAX)...")
        for i, s in enumerate(servos):
            s.max()
            print(f"  -> Servo on GPIO {PINS[i]} = 180°")
        time.sleep(2.0)

except KeyboardInterrupt:
    print("\n[STOP] User interrupted test. Disabling PWM output on all pins...")
    for s in servos:
        s.value = None  # None de-energizes the servo pin completely to stop buzzing
    print("Done.")
