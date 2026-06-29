import cv2
import numpy as np
from typing import List, Tuple, Optional

# ============================================================================
# GREEN DOT DETECTOR CLASS
# ============================================================================

class GreenDotDetector:
    def __init__(self, green_lower: np.ndarray, green_upper: np.ndarray,
                 min_area: int = 300, max_area: int = 5000):
        """
        Initialize green dot detector with HSV thresholds.

        Args:
            green_lower: Lower HSV bound for green detection
            green_upper: Upper HSV bound for green detection
            min_area: Minimum contour area threshold
            max_area: Maximum contour area threshold
        """
        self.green_lower = green_lower
        self.green_upper = green_upper
        self.min_area = min_area
        self.max_area = max_area

    def detect_dots(self, rectified_frame: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect green dots in rectified frame.

        Args:
            rectified_frame: Bird's-eye view frame from perspective warper

        Returns:
            List of (x, y) centroids of detected green dots
        """
        hsv = cv2.cvtColor(rectified_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.green_lower, self.green_upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        dots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_area <= area <= self.max_area:
                M = cv2.moments(contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    dots.append((cx, cy))

        return dots

    def evaluate_intersection(self, dots: List[Tuple[int, int]],
                            line_contour: Optional[np.ndarray],
                            threshold: int = 40) -> str:
        """
        Evaluate intersection decision based on green dot positions.

        Args:
            dots: List of detected green dot centroids
            line_contour: Main black line contour (optional)
            threshold: Spatial threshold for left/right decision

        Returns:
            Decision string: "TURN_LEFT", "TURN_RIGHT", "U_TURN", or "NONE"
        """
        if len(dots) == 0:
            return "NONE"

        x_line = 200

        if line_contour is not None:
            M = cv2.moments(line_contour)
            if M['m00'] > 0:
                x_line = int(M['m10'] / M['m00'])

        left_dots = [d for d in dots if d[0] < (x_line - threshold)]
        right_dots = [d for d in dots if d[0] > (x_line + threshold)]

        if len(left_dots) > 0 and len(right_dots) > 0:
            return "U_TURN"
        elif len(left_dots) > 0:
            return "TURN_LEFT"
        elif len(right_dots) > 0:
            return "TURN_RIGHT"
        else:
            return "NONE"
