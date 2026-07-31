#!/usr/bin/env python3
"""
PCA9685 I2C Servo Control Logic for Temuv2.5
This script tests 5 servos connected to channels 0, 1, 2, 3, and 4.

Prerequisites:
    pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
    (Make sure I2C is enabled in sudo raspi-config)
"""

import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

def main():
    print("Initializing I2C Bus...")
    # Initialize the I2C bus using the standard Raspberry Pi hardware I2C pins (SCL, SDA)
    i2c = busio.I2C(board.SCL, board.SDA)

    print("Connecting to PCA9685 at default address 0x40...")
    # Create the PCA9685 class instance.
    pca = PCA9685(i2c)

    # Set the PWM frequency to 50Hz, which is standard for RC servos.
    pca.frequency = 50

    print("Configuring Servos on Channels 0, 1, 2, 3, 4...")
    # Map the servos to the exact PCA9685 channels requested
    # min_pulse and max_pulse may need tuning depending on your exact 9g/MG996R servos
    # standard range is roughly 500us to 2500us for 0-180 degrees.
    servos = [
        servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500),
        servo.Servo(pca.channels[1], min_pulse=500, max_pulse=2500),
        servo.Servo(pca.channels[2], min_pulse=500, max_pulse=2500),
        servo.Servo(pca.channels[3], min_pulse=500, max_pulse=2500),
        servo.Servo(pca.channels[4], min_pulse=500, max_pulse=2500)
    ]

    try:
        print("Starting Servo Test Sequence (Press Ctrl+C to stop)...")
        while True:
            print("\nMoving all servos to 0 degrees (Min Position)")
            for i, s in enumerate(servos):
                s.angle = 0
                print(f"  -> Servo {i} at 0°")
            time.sleep(1.5)

            print("\nMoving all servos to 90 degrees (Center Position)")
            for i, s in enumerate(servos):
                s.angle = 90
                print(f"  -> Servo {i} at 90°")
            time.sleep(1.5)

            print("\nMoving all servos to 180 degrees (Max Position)")
            for i, s in enumerate(servos):
                s.angle = 180
                print(f"  -> Servo {i} at 180°")
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\nTest interrupted by user. Returning servos to center (90°)...")
        for s in servos:
            s.angle = 90
        
        # De-energize the servos by turning off the PWM signals completely
        # This prevents the servos from overheating if left idle holding a heavy load.
        print("De-energizing all PWM channels...")
        pca.deinit()
        print("Test Complete. Exiting.")

if __name__ == "__main__":
    main()
