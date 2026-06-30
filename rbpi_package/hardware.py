import time
import atexit

class RobotHardware:
    def __init__(self, left_pin=17, right_pin=27):
        """
        Initializes the robot hardware.
        Attempts to connect to ESP8266 via Serial using Hardware UART or USB Serial.
        """
        self.left_pin = left_pin
        self.right_pin = right_pin
        self.serial_port = None
        
        try:
            import serial
            for port in ['/dev/serial0', '/dev/ttyUSB0']:
                try:
                    print(f"[Hardware] Attempting to connect to Serial port: {port}")
                    self.serial_port = serial.Serial(
                        port=port,
                        baudrate=115200,
                        timeout=0.1
                    )
                    print(f"[Hardware] Successfully connected to serial port: {port}")
                    break
                except serial.SerialException as e:
                    print(f"[Hardware] Failed to connect to {port}: {e}")
        except ImportError:
            print("[Hardware] pyserial module not found. Running in mock serial mode.")

        atexit.register(self.cleanup)

    def set_speeds(self, left_speed, right_speed):
        """
        Sets the speed for left and right motors.
        Sends speeds to ESP8266 via Serial.
        Values are floats clamped between -1.0 and +1.0.
        """
        left_speed = max(-1.0, min(1.0, float(left_speed)))
        right_speed = max(-1.0, min(1.0, float(right_speed)))
        
        cmd = f"M:{left_speed:.4f},{right_speed:.4f}\n"
        print(f"[Hardware] Sending Serial Command: {cmd.strip()}")
        
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(cmd.encode('utf-8'))
                self.serial_port.flush()
            except Exception as e:
                # Catch serial.SerialException or other write errors gracefully
                print(f"[Hardware] Serial write error: {e}")

    def stop(self):
        print("[Hardware] Stopping robot.")
        self.set_speeds(0.0, 0.0)

    def cleanup(self):
        print("Cleaning up hardware...")
        self.stop()
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                print("[Hardware] Closed serial connection.")
            except Exception:
                pass
