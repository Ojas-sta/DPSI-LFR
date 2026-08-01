from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
import gpiozero
import time

gpiozero.Device.pin_factory = LGPIOFactory()

class BackpackManipulator:
    """
    Controls the 4-servo backpack manipulator and 1 sorting servo.
    """
    def __init__(self, grabber_pin: int, lifter_pin: int, sorter_pin: int, releaser_pin: int):
        self.grabber = AngularServo(grabber_pin, min_angle=-90, max_angle=90)
        self.lifter = AngularServo(lifter_pin, min_angle=-90, max_angle=90)
        self.sorter = AngularServo(sorter_pin, min_angle=-90, max_angle=90)
        self.releaser = AngularServo(releaser_pin, min_angle=-90, max_angle=90)
        
        # Initial safe positions
        self.reset_positions()

    def reset_positions(self):
        self.grabber.angle = -90 # Open
        self.lifter.angle = -90 # Down
        self.sorter.angle = 0 # Neutral
        self.releaser.angle = 90 # Closed
        
    def sequence_grab(self, is_live: bool):
        """
        Executes the grab, sort, and lift sequence.
        """
        # 1. Grab
        self.grabber.angle = 90 # Close
        time.sleep(0.5)
        
        # 2. Sort (Live vs Dead)
        if is_live:
            self.sorter.angle = 45 # Sort left/right based on logic
        else:
            self.sorter.angle = -45
        time.sleep(0.5)
        
        # 3. Lift to backpack
        self.lifter.angle = 90 # Up
        time.sleep(1.0)
        
        # Reset for next grab
        self.grabber.angle = -90
        self.lifter.angle = -90
        self.sorter.angle = 0
        
    def sequence_release(self):
        """
        Releases all balls from the backpack.
        """
        self.releaser.angle = -90 # Open door
        time.sleep(2.0)
        self.releaser.angle = 90 # Close door
