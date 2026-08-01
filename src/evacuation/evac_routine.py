import time

class EvacZoneManager:
    """
    Handles the Evacuation Zone 360-degree sweep strategy and MaixCAM YOLO alignment.
    """
    def __init__(self, drive_base, manipulator, imu_controller):
        self.drive = drive_base
        self.manipulator = manipulator
        self.nav = imu_controller
        self.balls_collected = 0
        self.max_balls = 3
        
    def enter_zone_and_sweep(self):
        """
        The main Evac Zone entry point.
        """
        # 1. Drive to approximate center
        self.drive.drive(0.4, 0.4)
        time.sleep(2.0)
        self.drive.stop()
        
        while self.balls_collected < self.max_balls:
            ball_detected, bounding_box = self._perform_360_scan()
            
            if ball_detected:
                self._align_and_capture(bounding_box)
            else:
                # No more balls found, head to evacuation point
                break
                
        self._evacuate_balls()
        
    def _perform_360_scan(self):
        """
        Slowly rotates 360 degrees while polling MaixCAM for YOLO ball detections.
        """
        start_heading = self.nav.imu.current_heading
        self.drive.drive(0.3, -0.3) # Slow spin
        
        while True:
            # Check if we've completed a full 360
            current = self.nav.imu.current_heading
            diff = (current - start_heading + 180) % 360 - 180
            # If we've rotated nearly a full circle and are back at the start
            # (Requires tracking total rotation, simplified here)
            
            # --- In a real implementation, poll the MaixCAM socket stream here ---
            # ball_detected, bbox = maixcam_stream.get_latest_yolo_detection()
            ball_detected = False
            bbox = None
            
            if ball_detected:
                self.drive.stop()
                return True, bbox
                
            time.sleep(0.05)
            
        self.drive.stop()
        return False, None
        
    def _align_and_capture(self, initial_bbox):
        """
        Uses bird's-eye view coordinates from MaixCAM to center the ball and grab it.
        """
        # 1. Alignment Loop (Visual Servoing)
        # In a real implementation, this loops continuously updating from the MaixCAM
        # until the ball is perfectly centered in the frame.
        is_aligned = True # Placeholder
        is_live_ball = True # Placeholder from MaixCAM classification
        
        if is_aligned:
            # 2. Trigger Manipulator Sequence
            self.manipulator.sequence_grab(is_live=is_live_ball)
            self.balls_collected += 1
            
    def _evacuate_balls(self):
        """
        Finds the evacuation corner and releases the backpack payload.
        """
        # 1. Find evac point (Visual or Ultrasonic)
        # 2. Drive to it
        # 3. Release
        self.manipulator.sequence_release()
