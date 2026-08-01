from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
import gpiozero

gpiozero.Device.pin_factory = LGPIOFactory()

class ObstacleSensor:
    def __init__(self, echo_pin: int, trigger_pin: int):
        # max_distance=2.0 meters
        self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=2.0)
        
    def get_distance_cm(self) -> float:
        """Returns distance in centimeters."""
        return self.sensor.distance * 100.0
