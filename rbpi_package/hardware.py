import time
import threading
import queue

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None

class RobotHardware:
    def __init__(self, left_pin=17, right_pin=27):
        self.left_pin = left_pin
        self.right_pin = right_pin
        
        self.left_speed = 0.0
        self.right_speed = 0.0
        
        self.trim_bias = 0.0
        
        self.steer_correction_enabled = True
        self.steer_assist_enabled = False
        
        self.is_calibrating = False
        self.calibration_progress = 0.0
        self.calibration_duration = 5.0
        
        self.yaw = 0.0
        
        self.telemetry_log = []
        self.telemetry_lock = threading.Lock()
        
        self.serial_port = None
        self.port_name = "/dev/serial0"
        self.is_connected = False
        self.is_mock = True
        
        self.command_queue = queue.Queue(maxsize=20)
        self.serial_running = True
        
        self._init_serial(self.port_name)
        
        self.serial_thread = threading.Thread(target=self.run_serial_worker, daemon=True)
        self.serial_thread.start()
        
    def _init_serial(self, port):
        if serial is None:
            self.is_mock = True
            return
            
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.serial_port = serial.Serial(port, 115200, timeout=0.1)
            self.port_name = port
            self.is_connected = True
            self.is_mock = False
        except (OSError, serial.SerialException):
            self.is_connected = False
            self.is_mock = True
            self.serial_port = None

    def switch_port(self, new_port):
        self._init_serial(new_port)
        self.log_telemetry(f"Switched serial port to {new_port}")

    def log_telemetry(self, msg):
        with self.telemetry_lock:
            self.telemetry_log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.telemetry_log) > 10:
                self.telemetry_log.pop(0)

    def run_serial_worker(self):
        """Dedicated thread for non-blocking UART communication to prevent CLI freezes."""
        while self.serial_running:
            # 1. Process RX (Incoming)
            if not self.is_mock and self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        line_bytes = self.serial_port.readline()
                        if line_bytes:
                            line = line_bytes.decode('utf-8', errors='ignore').strip()
                            if line:
                                self.log_telemetry(f"RX: {line}")
                                if line == "P_ACK":
                                    self.is_connected = True
                except Exception:
                    self.is_connected = False
            
            # 2. Process TX (Outgoing)
            try:
                # Block for a short time to keep the loop active but responsive
                cmd = self.command_queue.get(timeout=0.05)
                if not self.is_mock and self.serial_port and self.serial_port.is_open:
                    try:
                        self.serial_port.write(cmd.encode('utf-8'))
                        self.serial_port.flush()
                    except Exception as e:
                        self.is_connected = False
                        self.log_telemetry(f"TX Error: {e}")
            except queue.Empty:
                pass
                
    def set_speeds(self, left_speed, right_speed):
        self.left_speed = left_speed
        self.right_speed = right_speed
        
        # Apply trim bias correctly in both directions
        if self.trim_bias > 0:
            if self.right_speed > 0:
                self.right_speed = max(0.0, self.right_speed - self.trim_bias)
            elif self.right_speed < 0:
                self.right_speed = min(0.0, self.right_speed + self.trim_bias)
        elif self.trim_bias < 0:
            if self.left_speed > 0:
                self.left_speed = max(0.0, self.left_speed - abs(self.trim_bias))
            elif self.left_speed < 0:
                self.left_speed = min(0.0, self.left_speed + abs(self.trim_bias))
                
        # Send to queue (non-blocking)
        cmd = f"M:{self.right_speed:.4f},{self.left_speed:.4f}\n"
        try:
            if self.command_queue.full():
                self.command_queue.get_nowait()
            self.command_queue.put_nowait(cmd)
        except queue.Full:
            pass

    def send_arm(self, armed):
        if armed:
            self.set_speeds(0, 0)
        else:
            self.stop()

    def stop(self):
        self.set_speeds(0.0, 0.0)

    def adjust_trim(self, amount):
        self.trim_bias += amount
        self.trim_bias = max(-0.3, min(0.3, self.trim_bias))

    def toggle_steer_correction(self):
        self.steer_correction_enabled = not self.steer_correction_enabled

    def toggle_steer_assist(self):
        self.steer_assist_enabled = not self.steer_assist_enabled

    def reset_yaw(self):
        self.yaw = 0.0

    def skip_calibration(self):
        self.is_calibrating = False

    def cleanup(self):
        self.serial_running = False
        self.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
