from gpiozero import PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
import gpiozero

# Force lgpio factory for hardware DMA
gpiozero.Device.pin_factory = LGPIOFactory()

class IBT2Motor:
    """
    Controls a single DC motor using the IBT_2 motor driver.
    IBT_2 uses RPWM (Forward PWM) and LPWM (Reverse PWM).
    L_EN and R_EN must be HIGH to enable the respective directions.
    """
    def __init__(self, rpwm_pin: int, lpwm_pin: int, r_en_pin: int, l_en_pin: int, frequency: int = 1000):
        self._rpwm = PWMOutputDevice(rpwm_pin, frequency=frequency)
        self._lpwm = PWMOutputDevice(lpwm_pin, frequency=frequency)
        self._r_en = DigitalOutputDevice(r_en_pin)
        self._l_en = DigitalOutputDevice(l_en_pin)
        
        # Enable both sides of the H-bridge
        self._r_en.on()
        self._l_en.on()
        self.stop()

    def set_speed(self, speed: float):
        """
        Set motor speed from -1.0 (full reverse) to 1.0 (full forward).
        """
        speed = max(-1.0, min(1.0, speed)) # Clamp between -1.0 and 1.0
        
        if speed > 0:
            self._lpwm.value = 0.0
            self._rpwm.value = speed
        elif speed < 0:
            self._rpwm.value = 0.0
            self._lpwm.value = abs(speed)
        else:
            self.stop()

    def stop(self):
        self._rpwm.value = 0.0
        self._lpwm.value = 0.0

class DriveBase:
    """
    Controls the differential 4WD skid-steer drive base.
    """
    def __init__(self, left_motor: IBT2Motor, right_motor: IBT2Motor):
        self.left_motor = left_motor
        self.right_motor = right_motor

    def drive(self, left_speed: float, right_speed: float):
        self.left_motor.set_speed(left_speed)
        self.right_motor.set_speed(right_speed)
        
    def stop(self):
        self.left_motor.stop()
        self.right_motor.stop()
