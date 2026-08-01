import time
import cv2
import numpy as np

# HAL
from hal.motor import IBT2Motor, DriveBase
from hal.servo import BackpackManipulator
from hal.ultrasonic import ObstacleSensor

# Vision
from vision.line_follower import CroppedHorizonVision, RK4Kinematics
from vision.marker_detector import GreenMarkerDetector, IntersectionMasker

# Navigation & Evac
from navigation.imu_controller import ZeroDriftIMU, NavigationController
from evacuation.evac_routine import EvacZoneManager

def main():
    print("Temuv2.5 Initialization Sequence Started...")
    
    # Initialize Hardware
    left_motor = IBT2Motor(rpwm_pin=12, lpwm_pin=13, r_en_pin=5, l_en_pin=6)
    right_motor = IBT2Motor(rpwm_pin=18, lpwm_pin=19, r_en_pin=20, l_en_pin=21)
    drive_base = DriveBase(left_motor, right_motor)
    
    manipulator = BackpackManipulator(grabber_pin=22, lifter_pin=23, sorter_pin=24, releaser_pin=25)
    sonar = ObstacleSensor(echo_pin=26, trigger_pin=27)
    
    # Initialize Vision & Kinematics
    vision = CroppedHorizonVision(crop_percent=0.30)
    rk4 = RK4Kinematics(alpha=0.6, dt=0.05)
    marker_detector = GreenMarkerDetector()
    
    # Initialize Navigation
    imu = ZeroDriftIMU()
    nav_controller = NavigationController(drive_base, imu)
    evac_manager = EvacZoneManager(drive_base, manipulator, nav_controller)
    
    print("Hardware initialized. Starting control loop.")
    
    # Placeholder for PiCamera capture
    # cap = cv2.VideoCapture(0)
    
    try:
        while True:
            # 1. Read Sensors
            distance = sonar.get_distance_cm()
            
            # 2. Obstacle Avoidance (Hybrid logic)
            if distance < 15.0:
                print("Obstacle detected! Executing IMU sweep...")
                nav_controller.avoid_obstacle_sweep()
                continue
                
            # 3. Read Camera Frame (Simulated)
            # ret, frame = cap.read()
            # if not ret: continue
            
            # Simulated blank frame for structural completeness
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            
            # 4. Process Vision & Line Tracking
            raw_angle = vision.process_frame(frame)
            
            # 5. Apply RK4 Smoothing
            smooth_angle = rk4.smooth(raw_angle)
            
            # 6. Translate smoothed angle to differential drive speeds
            base_speed = 0.6
            left_speed = base_speed + (smooth_angle / 180.0)
            right_speed = base_speed - (smooth_angle / 180.0)
            
            drive_base.drive(left_speed, right_speed)
            
            # 7. Update IMU Zero-Drift Lock
            is_stopped = (left_speed == 0 and right_speed == 0)
            # Simulated gyro read
            sim_gyro_z = 0.0
            imu.update_from_stream(sim_gyro_z, is_stopped)
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Shutting down...")
        drive_base.stop()
        manipulator.reset_positions()

if __name__ == "__main__":
    main()
