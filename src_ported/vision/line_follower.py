import cv2
import numpy as np
from numba import njit

# ---------------------------------------------------------
# DIRECT PORT: Overengineering^2 (robot_v.3)
# ---------------------------------------------------------
@njit(cache=True)
def calculate_angle_numba(blackline, blackline_crop, last_bottom_point, average_line_point):
    """
    1-to-1 mathematical port from Overengineering^2 line_cam.py (Line 244)
    """
    camera_x = 320  # Adapted to our resolution (from 448)
    camera_y = 240  # Adapted to our resolution (from 252)
    
    poi = np.zeros((3, 2), dtype=np.int16)
    poi_no_crop = np.zeros((3, 2), dtype=np.int16)

    max_black_top = False
    
    # Check bounding box on cropped image
    black_crop_point = np.argwhere(blackline_crop)
    if len(black_crop_point) > 50:
        is_crop = True
        bottom_point = black_crop_point[:, 0].max()
        bottom_black = black_crop_point[black_crop_point[:, 0] == bottom_point]
        top_black = black_crop_point[black_crop_point[:, 0] == black_crop_point[:, 0].min()]

        bottom_mean = int(bottom_black[:, 1].mean())
        top_mean = int(top_black[:, 1].mean())

        poi[0] = [top_mean, black_crop_point[:, 0].min()]
        poi[1] = [bottom_mean, bottom_point]
        poi[2] = [bottom_mean, bottom_point]
    else:
        is_crop = False
        bottom_point = 0

    # Check bounding box on full image
    black_point = np.argwhere(blackline)
    if len(black_point) > 50:
        bottom_point_no_crop = black_point[:, 0].max()
        bottom_black_no_crop = black_point[black_point[:, 0] == bottom_point_no_crop]
        top_black_no_crop = black_point[black_point[:, 0] == black_point[:, 0].min()]

        bottom_mean_no_crop = int(bottom_black_no_crop[:, 1].mean())
        top_mean_no_crop = int(top_black_no_crop[:, 1].mean())

        poi_no_crop[0] = [top_mean_no_crop, black_point[:, 0].min()]
        poi_no_crop[1] = [bottom_mean_no_crop, bottom_point_no_crop]
        poi_no_crop[2] = [bottom_mean_no_crop, bottom_point_no_crop]
        
        # Chord shortcut logic limits
        if black_point[:, 0].min() < camera_y * 0.15 and len(top_black_no_crop) > (camera_x * 0.2):
            max_black_top = True

    return poi, poi_no_crop, is_crop, max_black_top, bottom_point

class CroppedHorizonVision:
    def __init__(self, camera_x: int = 320, camera_y: int = 240):
        self.camera_x = camera_x
        self.camera_y = camera_y
        self.last_bottom_point = [0, 0]
        self.average_line_point = camera_x // 2
        
    def process_frame(self, frame: np.ndarray) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        # 30% crop from the top to ignore local noise directly under bumper
        crop_start = int(self.camera_y * 0.3)
        cropped_thresh = thresh[crop_start:, :]
        
        # Pass pure boolean arrays to numba
        blackline = (thresh > 0)
        blackline_crop = (cropped_thresh > 0)
        
        poi, poi_no_crop, is_crop, max_black_top, bottom_point = calculate_angle_numba(
            blackline, blackline_crop, self.last_bottom_point, self.average_line_point
        )
        
        final_poi = poi[0] if is_crop and not max_black_top else poi_no_crop[0]
        
        # OVERENGINEERING^2 Steering Equation (Line 424)
        raw_angle = ((final_poi[0] - (self.camera_x / 2)) / (self.camera_x / 2)) * 180.0
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
        return self.alpha * (target - current)
        
    def smooth(self, target_angle: float) -> float:
        k1 = self.dt * self._derivative(target_angle, self.current_angle)
        k2 = self.dt * self._derivative(target_angle, self.current_angle + 0.5 * k1)
        k3 = self.dt * self._derivative(target_angle, self.current_angle + 0.5 * k2)
        k4 = self.dt * self._derivative(target_angle, self.current_angle + k3)
        
        self.current_angle += (k1 + 2*k2 + 2*k3 + k4) / 6.0
        return self.current_angle
