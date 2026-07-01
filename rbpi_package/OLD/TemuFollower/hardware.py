import time
import atexit

class RobotHardware:
    def __init__(self, left_pin=17, right_pin=27):
        """
        Initializes the robot hardware.
        Uses pin 17 for left motor and pin 27 for right motor.
        """
        self.left_pin = left_pin
        self.right_pin = right_pin
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.has_hardware = True
            
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setwarnings(False)
            
            # Setup Left Motor
            self.GPIO.setup(self.left_pin, self.GPIO.OUT)
            
            # Setup Right Motor
            self.GPIO.setup(self.right_pin, self.GPIO.OUT)
            
            atexit.register(self.cleanup)
        except ImportError:
            print("RPi.GPIO not found. Running in simulation/mock mode.")
            self.has_hardware = False

    def send_analog_voltage(self, pin, voltage):
        """
        Sends a literal analog voltage to the specified pin.
        Note: Standard RPi.GPIO does not support true analog out. 
        This is a placeholder for your specific DAC or analog hardware library.
        """
        if not self.has_hardware:
            return
            
        # Example of how this might be handled by an analog library:
        # custom_analog_library.write(pin, voltage)
        
        # We will attempt to send it via standard GPIO (this usually only works for 1/0)
        # Please replace this inner call with your specific DAC / Analog-out library
        try:
            # If you are using a library that patched RPi.GPIO to support analog floats
            self.GPIO.output(pin, voltage)
        except Exception as e:
            pass # Handle strictly digital GPIO error

    def set_speeds(self, left_speed, right_speed):
        """
        Sets the speed for left and right motors.
        Speeds should be floats between 0.0 and 1.0.
        Output voltage values are calculated by multiplying by 3.3 (0-3.3 range).
        """
        # Clamp values between 0.0 and 1.0
        left_speed = max(0.0, min(1.0, float(left_speed)))
        right_speed = max(0.0, min(1.0, float(right_speed)))
        
        # Calculate pin values (0 - 3.3)
        left_pin_value = left_speed * 3.3
        right_pin_value = right_speed * 3.3
        
        print(f"[Hardware] Outputting {left_pin_value:.2f}V to Pin {self.left_pin} | {right_pin_value:.2f}V to Pin {self.right_pin}")
        
        if not self.has_hardware:
            return
            
        # Send literal voltage as an analog value
        self.send_analog_voltage(self.left_pin, left_pin_value)
        self.send_analog_voltage(self.right_pin, right_pin_value)

    def stop(self):
        if not self.has_hardware:
            return
        self.send_analog_voltage(self.left_pin, 0.0)
        self.send_analog_voltage(self.right_pin, 0.0)

    def cleanup(self):
        print("Cleaning up hardware...")
        self.stop()
        if self.has_hardware:
            self.GPIO.cleanup()
