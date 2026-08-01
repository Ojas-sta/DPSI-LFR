import time

class ZeroDriftIMU:
    """
    Handles the IMU data stream from the MaixCAM Pro.
    Implements a zero-drift lock by zeroing gyro bias when the robot is stopped.
    """
    def __init__(self):
        self.current_heading = 0.0
        self.gyro_bias_z = 0.0
        self.last_update_time = time.time()
        
    def update_from_stream(self, raw_gyro_z: float, is_robot_stopped: bool):
        """
        Called continuously with new data from the MaixCAM serial/socket stream.
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Zero-Drift Complementary Filter Logic
        if is_robot_stopped:
            # If the Pi commands 0 speed, the robot is physically still.
            # Any gyro reading here is pure drift/bias.
            # We aggressively lock the bias to this value to nullify it.
            self.gyro_bias_z = (self.gyro_bias_z * 0.9) + (raw_gyro_z * 0.1)
            return self.current_heading
            
        # Integrate gyro to heading (subtracting the locked bias)
        true_angular_velocity = raw_gyro_z - self.gyro_bias_z
        self.current_heading += true_angular_velocity * dt
        
        # Normalize to 0-360
        self.current_heading = self.current_heading % 360.0
        return self.current_heading

class NavigationController:
    """
    Executes precise maneuvers using the Zero-Drift IMU heading.
    """
    def __init__(self, drive_base, imu: ZeroDriftIMU):
        self.drive = drive_base
        self.imu = imu
        
    def execute_locked_spin(self, target_angle_delta: float, speed: float = 0.5):
        """
        Spins exactly target_angle_delta degrees (e.g., 90 for Green Marker).
        """
        start_heading = self.imu.current_heading
        target_heading = (start_heading + target_angle_delta) % 360.0
        
        direction = 1 if target_angle_delta > 0 else -1
        self.drive.drive(speed * direction, -speed * direction) # Spin in place
        
        while True:
            current = self.imu.current_heading
            # Calculate shortest angular distance
            diff = (target_heading - current + 180) % 360 - 180
            if abs(diff) < 2.0: # 2 degree tolerance
                break
            time.sleep(0.01)
            
        self.drive.stop()
        
    def avoid_obstacle_sweep(self):
        """
        Hybrid Obstacle Avoidance: Executes a predictable 180-degree half-circle sweep 
        around an obstacle (e.g. water bottle) using IMU data to reacquire the line.
        """
        # 1. Stop and lock IMU bias briefly
        self.drive.stop()
        time.sleep(0.2) 
        
        # 2. Turn 90 degrees left (away from obstacle)
        self.execute_locked_spin(-90.0)
        
        # 3. Drive forward slightly
        self.drive.drive(0.5, 0.5)
        time.sleep(1.0)
        
        # 4. Turn 90 degrees right (parallel to original path)
        self.execute_locked_spin(90.0)
        
        # 5. Drive past the obstacle
        self.drive.drive(0.5, 0.5)
        time.sleep(1.5)
        
        # 6. Turn 90 degrees right (back towards line)
        self.execute_locked_spin(90.0)
        
        # 7. Drive until downward camera sees line again (handled in main loop)
        # This is just the basic open-loop IMU sweep logic.
