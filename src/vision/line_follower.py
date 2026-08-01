import cv2
import numpy as np

class CroppedHorizonVision:
    """
    Implements the Overengineering² 'Cropped Horizon' and 'Chord Shortcutting' logic.
    """
    def __init__(self, camera_x: int = 320, camera_y: int = 240, crop_percent: float = 0.30):
        self.camera_x = camera_x
        self.camera_y = camera_y
        
        # We crop out the bottom 'crop_percent' of the image to ignore local S-curves/zig-zags
        self.crop_y_start = 0
        self.crop_y_end = int(self.camera_y * (1.0 - crop_percent))
        
    def process_frame(self, frame: np.ndarray) -> float:
        """
        Processes a raw BGR frame and returns the target steering angle (degrees).
        Uses geometric moments and POI (Point of Interest) logic.
        """
        # Convert to grayscale and threshold (assuming black line on white background)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold (Adjust values based on physical lighting)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        # 1. Uncropped Analysis (To find exit points on the far left/right for 90-deg step turns)
        contours_full, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 2. Cropped Horizon Analysis (To ignore local zig-zags)
        cropped_thresh = thresh[self.crop_y_start:self.crop_y_end, :]
        contours_crop, _ = cv2.findContours(cropped_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours_full:
            return 0.0 # Line lost, default straight or last known
            
        # Get largest contour
        c_full = max(contours_full, key=cv2.contourArea)
        
        # Calculate full bounding box to check if line exits side (Step Turn detection)
        x, y, w, h = cv2.boundingRect(c_full)
        
        # Overengineering POI (Point of Interest) Logic
        # Default final_poi is the center of the bounding box's top edge in the cropped view
        if contours_crop:
            c_crop = max(contours_crop, key=cv2.contourArea)
            M_crop = cv2.moments(c_crop)
            if M_crop["m00"] > 0:
                cx_crop = int(M_crop["m10"] / M_crop["m00"])
            else:
                cx_crop = self.camera_x // 2
            
            # The top horizon exit point (ignoring the bottom 30% of the image)
            final_poi_x = cx_crop
        else:
            final_poi_x = self.camera_x // 2
            
        # Chord Shortcutting Logic (90-deg Step Turns)
        # If the line exits heavily to the left or right of the frame (w is very large compared to h)
        if w > self.camera_x * 0.6: 
            # We have a step turn. Target the far exit point (Chord Shortcutting)
            # Find the leftmost or rightmost point of the full contour
            leftmost = tuple(c_full[c_full[:,:,0].argmin()][0])
            rightmost = tuple(c_full[c_full[:,:,0].argmax()][0])
            
            # If the mass of the contour is mostly on the left
            if x + (w/2) < self.camera_x / 2:
                final_poi_x = leftmost[0] # Target far left exit
            else:
                final_poi_x = rightmost[0] # Target far right exit
                
        # Calculate steering angle based on final POI
        # angle = ((final_poi_x - center) / center) * 180
        center = self.camera_x / 2.0
        raw_angle = ((final_poi_x - center) / center) * 180.0
        
        return raw_angle

class RK4Kinematics:
    """
    Applies 4th-Order Runge-Kutta smoothing to the raw steering angle,
    acting as a mathematical low-pass spatial filter (Trajectory Hysteresis).
    """
    def __init__(self, alpha: float = 0.5, dt: float = 0.05):
        self.alpha = alpha
        self.dt = dt
        self.current_angle = 0.0
        
    def _derivative(self, target: float, current: float) -> float:
        # Rate of change towards target
        return self.alpha * (target - current)
        
    def smooth(self, target_angle: float) -> float:
        """
        Takes the raw targeted angle and applies RK4 smoothing.
        """
        k1 = self.dt * self._derivative(target_angle, self.current_angle)
        k2 = self.dt * self._derivative(target_angle, self.current_angle + 0.5 * k1)
        k3 = self.dt * self._derivative(target_angle, self.current_angle + 0.5 * k2)
        k4 = self.dt * self._derivative(target_angle, self.current_angle + k3)
        
        self.current_angle += (k1 + 2*k2 + 2*k3 + k4) / 6.0
        return self.current_angle
