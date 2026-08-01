import cv2
import numpy as np
from numba import njit

# Numba JIT compiled function for ultra-fast HSV thresholding
@njit
def fast_hsv_green_threshold(hsv_image: np.ndarray, lower_h: int, upper_h: int, 
                             lower_s: int, upper_s: int, lower_v: int, upper_v: int) -> np.ndarray:
    """
    Iterates through the HSV image and returns a binary mask of green pixels.
    Numba @njit makes this run at C-like speeds.
    """
    rows, cols, _ = hsv_image.shape
    mask = np.zeros((rows, cols), dtype=np.uint8)
    
    for y in range(rows):
        for x in range(cols):
            h, s, v = hsv_image[y, x]
            if (lower_h <= h <= upper_h) and (lower_s <= s <= upper_s) and (lower_v <= v <= upper_v):
                mask[y, x] = 255
                
    return mask

class GreenMarkerDetector:
    def __init__(self, camera_x: int = 320, camera_y: int = 240):
        self.camera_x = camera_x
        self.camera_y = camera_y
        
        # HSV bounds for RoboCup green
        self.lower_green = (40, 50, 50)
        self.upper_green = (80, 255, 255)
        
    def detect_and_validate(self, frame: np.ndarray, black_line_mask: np.ndarray):
        """
        Detects green markers and validates them using the Overengineering 4-Side ROI Probing.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Fast HSV extraction
        green_mask = fast_hsv_green_threshold(hsv, 
                                              self.lower_green[0], self.upper_green[0],
                                              self.lower_green[1], self.upper_green[1],
                                              self.lower_green[2], self.upper_green[2])
                                              
        # Find green blobs
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_markers = []
        
        for c in contours:
            if cv2.contourArea(c) < 200: # Filter small noise
                continue
                
            x, y, w, h = cv2.boundingRect(c)
            
            # OVERENGINEERING 4-SIDE ROI PROBING
            # We probe 4 small 5x5 pixel regions around the green box to check if it touches the black line.
            # True green markers MUST touch the black line on specific sides.
            
            # Probe coordinates (safely constrained to image bounds)
            probe_dist = 5
            top_roi    = black_line_mask[max(0, y - probe_dist) : y, x : x + w]
            bottom_roi = black_line_mask[y + h : min(self.camera_y, y + h + probe_dist), x : x + w]
            left_roi   = black_line_mask[y : y + h, max(0, x - probe_dist) : x]
            right_roi  = black_line_mask[y : y + h, x + w : min(self.camera_x, x + w + probe_dist)]
            
            # Count black pixels in each ROI
            touches_top    = np.count_nonzero(top_roi) > 5
            touches_bottom = np.count_nonzero(bottom_roi) > 5
            touches_left   = np.count_nonzero(left_roi) > 5
            touches_right  = np.count_nonzero(right_roi) > 5
            
            # Validation Logic
            is_valid = False
            turn_direction = None
            
            # Example logic: A left marker should touch the line on its RIGHT side.
            if touches_right and not touches_left:
                is_valid = True
                turn_direction = "LEFT"
            elif touches_left and not touches_right:
                is_valid = True
                turn_direction = "RIGHT"
            elif touches_left and touches_right:
                is_valid = True
                turn_direction = "TURNAROUND"
                
            if is_valid:
                valid_markers.append({
                    "rect": (x, y, w, h),
                    "direction": turn_direction
                })
                
        return valid_markers

class IntersectionMasker:
    """
    Implements CatBot-Neo's 'CutMaskWithLine' logic.
    """
    @staticmethod
    def cut_mask_with_line(line_mask: np.ndarray, pt1: tuple, pt2: tuple, thickness: int = 15) -> np.ndarray:
        """
        Slices the binary mask with a line equation to block out false branches.
        Draws a thick black line over the given path to sever the intersection.
        """
        masked = line_mask.copy()
        cv2.line(masked, pt1, pt2, 0, thickness)
        return masked
