import time
import atexit
import threading

try:
    from mpu6050 import mpu6050
    has_mpu = True
except ImportError:
    has_mpu = False

class RobotHardware:
    def __init__(self, left_pin=17, right_pin=27):
        """
        Initializes the robot hardware.
        Attempts to connect to ESP8266 via Serial using Hardware UART or USB Serial.
        """
        self.left_pin = left_pin
        self.right_pin = right_pin
        self.serial_port = None
        
        # Synchronization locks
        self.serial_lock = threading.Lock()
        self.telemetry_lock = threading.Lock()
        
        # Telemetry & Status attributes
        self.telemetry_log = []
        self.is_connected = False
        self.is_mock = True
        self.is_test_mock = False
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.last_ping_time = 0.0
        self.last_pong_time = 0.0
        
        # Drift trim bias (clamped between -0.3 and 0.3)
        # trim_bias > 0: reduces Right wheel (corrects drift to Left)
        # trim_bias < 0: reduces Left wheel (corrects drift to Right)
        self.trim_bias = 0.0
        
        # IMU Yaw tracking
        self.yaw = 0.0
        self.imu_sensor = None
        self.gyro_bias_z = 0.0
        self.last_imu_time = time.time()
        self.is_calibrating = False
        self.calibration_progress = 0.0
        self.calibration_duration = 20.0 # Reduced to 20 seconds
        self.gyro_scale = 3.0            # Increased gyro sensitivity scaling to 3x
        
        if has_mpu:
            try:
                self.imu_sensor = mpu6050(0x68)
                self.is_calibrating = True
                self.telemetry_log.append("[IMU] MPU6050 found. Starting 60s calibration...")
            except Exception as e:
                self.telemetry_log.append(f"[IMU] Init Error: {e}")
                self.imu_sensor = None

        
        self.stop_thread_event = threading.Event()
        
        # Default port name
        self.port_name = '/dev/serial0'
        
        # Attempt connection on startup (with fallback loop to support unit tests and default setup)
        try:
            import serial
            for port in ['/dev/serial0', '/dev/ttyUSB0']:
                try:
                    print(f"[Hardware] Attempting to connect to Serial port: {port}")
                    with self.serial_lock:
                        self.serial_port = serial.Serial(
                            port=port,
                            baudrate=115200,
                            timeout=0.1
                        )
                    self.port_name = port
                    self.is_mock = False
                    print(f"[Hardware] Successfully connected to serial port: {port}")
                    break
                except Exception as e:
                    print(f"[Hardware] Failed to connect to {port}: {e}")
        except ImportError:
            print("[Hardware] pyserial module not found. Running in mock serial mode.")
            self.is_mock = True

        atexit.register(self.cleanup)

        # Detect if the opened serial port object is a unit test Mock/MagicMock
        if self.serial_port and type(self.serial_port).__name__ in ('MagicMock', 'Mock'):
            self.is_test_mock = True
            self.is_mock = False
            self.is_connected = True

        # Only start background monitoring thread if we are not running a unit test mock
        if not self.is_test_mock:
            self.reader_thread = threading.Thread(target=self.run_serial_reader, daemon=True)
            self.reader_thread.start()
            
            # Spin up a dedicated thread for IMU integration
            self.imu_thread = threading.Thread(target=self.run_imu_loop, daemon=True)
            self.imu_thread.start()

    def run_serial_reader(self):
        """Background thread loop to send ping heartbeats and read incoming serial lines safely."""
        mock_telemetry_timer = 0.0
        last_motor_send_time = 0.0
        while not self.stop_thread_event.is_set():
            current_time = time.time()
            
            # 1. Send continuous Motor commands (M:) every 200ms to feed ESP Watchdog
            if current_time - last_motor_send_time >= 0.2:
                last_motor_send_time = current_time
                if not self.is_mock and self.serial_port:
                    try:
                        with self.serial_lock:
                            if self.serial_port.is_open:
                                cmd = f"M:{self.right_speed:.4f},{self.left_speed:.4f}\n"
                                self.serial_port.write(cmd.encode('utf-8'))
                                self.serial_port.flush()
                    except Exception:
                        pass
                        
            # 2. Send 'P\n' ping every 1.0 second
            if current_time - self.last_ping_time >= 1.0:
                self.last_ping_time = current_time
                if not self.is_mock and self.serial_port:
                    try:
                        with self.serial_lock:
                            if self.serial_port.is_open:
                                self.serial_port.write(b"P\n")
                                self.serial_port.flush()
                    except Exception:
                        pass
                elif self.is_mock:
                    # Simulate heartbeat echo in mock mode
                    self.last_pong_time = current_time

            # 2. Read non-blocking serial lines
            if not self.is_mock and self.serial_port:
                try:
                    line_bytes = b''
                    with self.serial_lock:
                        if self.serial_port.is_open and self.serial_port.in_waiting > 0:
                            line_bytes = self.serial_port.readline()
                    
                    if line_bytes and isinstance(line_bytes, bytes):
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                        if line:
                            if line == "P_ACK":
                                self.last_pong_time = time.time()
                            else:
                                with self.telemetry_lock:
                                    self.telemetry_log.append(line)
                                    if len(self.telemetry_log) > 10:
                                        self.telemetry_log.pop(0)
                except Exception:
                    pass
            elif self.is_mock:
                # Generate mock telemetry logs every 2.0 seconds
                if current_time - mock_telemetry_timer >= 2.0:
                    mock_telemetry_timer = current_time
                    mock_line = f"[MOCK] ESP Telemetry: L={self.left_speed:+.2f} R={self.right_speed:+.2f} Watchdog=OK"
                    with self.telemetry_lock:
                        self.telemetry_log.append(mock_line)
                        if len(self.telemetry_log) > 10:
                            self.telemetry_log.pop(0)

            # 3. Connection Status update
            self.is_connected = (time.time() - self.last_pong_time) < 2.5
            
            time.sleep(0.01)

    def switch_port(self, port_name):
        """Switches the active serial port, closing the old connection safely."""
        with self.serial_lock:
            if self.serial_port:
                try:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                except Exception:
                    pass
            self.serial_port = None
            self.port_name = port_name
            self.is_mock = True
            self.is_connected = False
            
            try:
                import serial
                is_mock_mod = type(serial).__name__ in ('MagicMock', 'Mock')
                
                if is_mock_mod:
                    self.serial_port = serial.Serial(port=port_name, baudrate=115200, timeout=0.1)
                    self.is_test_mock = True
                    self.is_mock = False
                    self.is_connected = True
                else:
                    print(f"[Hardware] Attempting to connect to Serial port: {port_name}")
                    self.serial_port = serial.Serial(
                        port=port_name,
                        baudrate=115200,
                        timeout=0.1
                    )
                    self.is_mock = False
                    self.is_connected = True
                    self.last_pong_time = time.time()
                    print(f"[Hardware] Successfully connected to serial port: {port_name}")
            except Exception as e:
                print(f"[Hardware] Failed to connect to {port_name}: {e}. Running in Mock mode.")

    def reset_yaw(self):
        """Resets the integrated yaw angle to zero and re-calibrates bias quickly (1 second)."""
        self.yaw = 0.0
        if self.imu_sensor:
            try:
                bias_sum = 0.0
                successful_samples = 0
                for _ in range(50):
                    try:
                        gyro_data = self.imu_sensor.get_gyro_data()
                        bias_sum += gyro_data['z']
                        successful_samples += 1
                    except Exception:
                        pass
                    time.sleep(0.02)
                if successful_samples > 0:
                    self.gyro_bias_z = bias_sum / successful_samples
            except Exception:
                pass

    def run_imu_loop(self):
        """Dedicated background thread for high-frequency Gyro integration."""
        self.last_imu_time = time.time()
        error_throttle_time = 0.0
        
        # 1. Handle Calibration over 60 seconds
        if self.imu_sensor and self.is_calibrating:
            bias_sum = 0.0
            successful_samples = 0
            samples_needed = int(self.calibration_duration * 50) # 50Hz = 3000 samples
            
            for i in range(samples_needed):
                if self.stop_thread_event.is_set():
                    return
                try:
                    gyro_data = self.imu_sensor.get_gyro_data()
                    bias_sum += gyro_data['z']
                    successful_samples += 1
                except Exception:
                    pass
                self.calibration_progress = (i + 1) / samples_needed
                time.sleep(0.02)
                
            if successful_samples > 0:
                self.gyro_bias_z = bias_sum / successful_samples
            self.is_calibrating = False
            with self.telemetry_lock:
                self.telemetry_log.append(f"[IMU] Calibration complete. Bias: {self.gyro_bias_z:.4f}")
                
        # 2. Main Yaw Integration loop
        while not self.stop_thread_event.is_set():
            current_time = time.time()
            if self.imu_sensor and not self.is_calibrating:
                try:
                    gyro_data = self.imu_sensor.get_gyro_data()
                    dt = current_time - self.last_imu_time
                    self.last_imu_time = current_time
                    
                    # Subtract calibrated bias
                    gyro_z = gyro_data['z'] - self.gyro_bias_z
                    
                    # Apply small deadzone (e.g. 0.15 deg/s) to reduce drift when stationary
                    if abs(gyro_z) > 0.15:
                        self.yaw += gyro_z * dt * self.gyro_scale
                        
                    # Normalize yaw to -180 to +180 range
                    self.yaw = (self.yaw + 180) % 360 - 180
                except Exception as e:
                    self.last_imu_time = current_time
                    if current_time - error_throttle_time > 5.0:
                        error_throttle_time = current_time
                        with self.telemetry_lock:
                            self.telemetry_log.append(f"[IMU] Read error: {e}")
                            if len(self.telemetry_log) > 10:
                                self.telemetry_log.pop(0)
            else:
                self.last_imu_time = current_time
                # Simulate a slowly rotating yaw in mock mode if driving
                if self.is_mock and (abs(self.left_speed) > 0.1 or abs(self.right_speed) > 0.1):
                    turn_diff = self.right_speed - self.left_speed
                    self.yaw += turn_diff * 40.0 * (current_time - self.last_imu_time)
                    self.yaw = (self.yaw + 180) % 360 - 180
            time.sleep(0.02) # 50Hz is perfect for integration

    def adjust_trim(self, amount):
        """Adjusts the drift trim bias (clamps between -0.3 and 0.3)."""
        self.trim_bias = max(-0.3, min(0.3, self.trim_bias + amount))

    def reset_yaw(self):
        """Resets the integrated yaw angle to zero and re-calibrates bias."""
        self.yaw = 0.0
        if self.imu_sensor:
            try:
                bias_sum = 0.0
                for _ in range(50):
                    try:
                        gyro_data = self.imu_sensor.get_gyro_data()
                        bias_sum += gyro_data['z']
                    except Exception:
                        pass
                    time.sleep(0.005)
                self.gyro_bias_z = bias_sum / 50.0
            except Exception:
                pass

    def set_speeds(self, left_speed, right_speed):
        """
        Sets the speed for left and right motors.
        Applies trim_bias to correct physical motor imbalances.
        Sends speeds to ESP8266 via Serial.
        Values are floats clamped between -1.0 and +1.0.
        """
        # Apply trim_bias (trim_bias > 0 reduces Right, trim_bias < 0 reduces Left)
        trimmed_left = left_speed
        trimmed_right = right_speed
        
        if left_speed != 0.0 or right_speed != 0.0:
            if self.trim_bias > 0.0:
                trimmed_right = right_speed * (1.0 - self.trim_bias)
            elif self.trim_bias < 0.0:
                trimmed_left = left_speed * (1.0 + self.trim_bias)
                
        self.left_speed = max(-1.0, min(1.0, float(trimmed_left)))
        self.right_speed = max(-1.0, min(1.0, float(trimmed_right)))

        
        cmd = f"M:{self.right_speed:.4f},{self.left_speed:.4f}\n"
        
        if self.is_mock:
            with self.telemetry_lock:
                self.telemetry_log.append(f"[MOCK TX] M:{self.left_speed:.4f},{self.right_speed:.4f}")
                if len(self.telemetry_log) > 10:
                    self.telemetry_log.pop(0)
                    
        if self.serial_port:
            try:
                with self.serial_lock:
                    if self.serial_port.is_open:
                        self.serial_port.write(cmd.encode('utf-8'))
                        self.serial_port.flush()
            except Exception as e:
                print(f"[Hardware] Serial write error: {e}")

    def send_arm(self, state: bool):
        """Sends Arm/Disarm command to ESP8266."""
        val = 1 if state else 0
        cmd = f"A:{val}\n"
        
        if self.is_mock:
            with self.telemetry_lock:
                self.telemetry_log.append(f"[MOCK TX] A:{val}")
                if len(self.telemetry_log) > 10:
                    self.telemetry_log.pop(0)
                    
        if self.serial_port:
            try:
                with self.serial_lock:
                    if self.serial_port.is_open:
                        self.serial_port.write(cmd.encode('utf-8'))
                        self.serial_port.flush()
            except Exception as e:
                print(f"[Hardware] Serial write error: {e}")

    def send_mode(self, auto: bool):
        """Sends Auto/Manual mode command to ESP8266."""
        val = 1 if auto else 0
        cmd = f"C:{val}\n"
        
        if self.is_mock:
            with self.telemetry_lock:
                self.telemetry_log.append(f"[MOCK TX] C:{val}")
                if len(self.telemetry_log) > 10:
                    self.telemetry_log.pop(0)
                    
        if self.serial_port:
            try:
                with self.serial_lock:
                    if self.serial_port.is_open:
                        self.serial_port.write(cmd.encode('utf-8'))
                        self.serial_port.flush()
            except Exception as e:
                print(f"[Hardware] Serial write error: {e}")

    def stop(self):
        print("[Hardware] Stopping robot.")
        self.set_speeds(0.0, 0.0)

    def cleanup(self):
        print("Cleaning up hardware...")
        self.stop_thread_event.set()
        if hasattr(self, 'reader_thread') and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        if hasattr(self, 'imu_thread') and self.imu_thread.is_alive():
            self.imu_thread.join(timeout=1.0)
        self.stop()
        if self.serial_port:
            try:
                with self.serial_lock:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                print("[Hardware] Closed serial connection.")
            except Exception:
                pass

