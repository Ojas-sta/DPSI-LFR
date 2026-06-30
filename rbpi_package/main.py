import time
import cv2
import math
from vision import VisionAgent
from control import ControlAgent
from hardware import RobotHardware
from feedback import FeedbackController

# Try to import mpu6050 for stuck detection
try:
    from mpu6050 import mpu6050
    has_mpu = True
except ImportError:
    print("Warning: mpu6050 library not found. Stuck detection will run in mock mode.")
    has_mpu = False


class StuckDetector:
    def __init__(self, sensor, threshold_gyro=5.0, threshold_accel=0.1, duration=1.5):
        """
        Detects if the robot is stuck by checking if commanded speed is non-zero,
        but physical motion (acceleration changes or rotational velocity) remains below thresholds.
        """
        self.sensor = sensor
        self.threshold_gyro = threshold_gyro
        self.threshold_accel = threshold_accel
        self.duration = duration
        self.stuck_start_time = None
        self.last_accel = None
        
    def is_stuck(self, left_speed, right_speed):
        if not self.sensor:
            return False
            
        # If the robot is not commanded to move, it's not "stuck"
        if abs(left_speed) < 0.1 and abs(right_speed) < 0.1:
            self.stuck_start_time = None
            return False
            
        try:
            accel_data = self.sensor.get_accel_data() # returns dict: {'x': val, 'y': val, 'z': val}
            gyro_data = self.sensor.get_gyro_data()   # returns dict: {'x': val, 'y': val, 'z': val}
            
            # Gyro rotation magnitude
            g_magnitude = math.sqrt(gyro_data['x']**2 + gyro_data['y']**2 + gyro_data['z']**2)
            
            # Accelerometer difference to capture change in movement
            if self.last_accel is not None:
                accel_diff = math.sqrt(
                    (accel_data['x'] - self.last_accel['x'])**2 +
                    (accel_data['y'] - self.last_accel['y'])**2 +
                    (accel_data['z'] - self.last_accel['z'])**2
                )
            else:
                accel_diff = 0.0
            self.last_accel = accel_data
            
            # Check if gyro and accel rates are below static thresholds
            if g_magnitude < self.threshold_gyro and accel_diff < self.threshold_accel:
                if self.stuck_start_time is None:
                    self.stuck_start_time = time.time()
                elif time.time() - self.stuck_start_time > self.duration:
                    return True
            else:
                self.stuck_start_time = None
                
        except Exception as e:
            print(f"[IMU] Error reading MPU6050: {e}")
            
        return False


def main():
    print("Initializing Robot Modules...")
    
    # Initialize Hardware
    hw = RobotHardware(left_pin=17, right_pin=27)
    
    # Initialize Vision
    vision = VisionAgent(resolution=(320, 240))
    
    # Initialize Control
    control = ControlAgent(target_x_center=160, base_speed=1.0)
    
    # Initialize Feedback Controller (Red LED Pin 5, Green LED Pin 6, Buzzer Pin 13)
    feedback = FeedbackController(red_pin=5, green_pin=6, buzzer_pin=13)
    
    # Initialize MPU6050 sensor
    mpu_sensor = None
    if has_mpu:
        try:
            mpu_sensor = mpu6050(0x68)
            print("[IMU] MPU6050 initialized successfully.")
        except Exception as e:
            print(f"[IMU] Failed to initialize MPU6050: {e}")
            
    stuck_detector = StuckDetector(mpu_sensor)
    
    # Signal that system is armed/ready
    feedback.indicate_armed()
    print("Robot initialized. Starting main loop.")
    
    try:
        # Give camera time to warm up
        time.sleep(1.0)
        
        print("[Main] Starting continuous camera feed...")
        for frame in vision.get_frame():
            # 1. Process visual input
            vision_data = vision.process_frame(frame)
            
            # 2. Compute non-linear PID control / state machine
            left_speed, right_speed = control.calculate_speeds(vision_data)
            
            # 3. Check for Stuck State via IMU
            if stuck_detector.is_stuck(left_speed, right_speed):
                print("[Main] STUCK STATE DETECTED! Stopping motors and triggering rapid alarm.")
                left_speed, right_speed = 0.0, 0.0
                feedback.indicate_stuck_alarm()
            
            # 4. Check for Visual Marker Detections
            if vision_data.get("red_dot_detected"):
                feedback.action_red_dot()
                left_speed, right_speed = 0.0, 0.0 # Emergency brake on red dot/stop line
            elif vision_data.get("green_dot_detected"):
                feedback.action_green_dot()
            
            # 5. Actuate hardware (sends command via Serial)
            print(f"[Main] Sending to Hardware -> Left Speed: {left_speed:.2f}, Right Speed: {right_speed:.2f}")
            hw.set_speeds(left_speed, right_speed)
            
            # 6. Display for debugging
            cv2.imshow("Robot Vision Live", frame)
            
            if vision_data["cnn_layers"] is not None:
                if "Black_Mask" in vision_data["cnn_layers"]:
                    cv2.imshow("Vision Layer: Black Line Isolation", vision_data["cnn_layers"]["Black_Mask"])
                if "Mask_Closed" in vision_data["cnn_layers"]:
                    cv2.imshow("Vision Layer: Mask Closed (Morphology)", vision_data["cnn_layers"]["Mask_Closed"])
            
            # Exit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Main] 'q' pressed. Exiting loop.")
                break
            
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Cleanup and safe stop
        hw.cleanup()
        feedback.cleanup()
        cv2.destroyAllWindows()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
