import cv2
import numpy as np

class RedDotDetector:
    def __init__(self):
        # Red hue wraps around in OpenCV (0-10 and 170-180)
        self.lower_red1 = np.array([0, 100, 100])
        self.upper_red1 = np.array([10, 255, 255])
        
        self.lower_red2 = np.array([160, 100, 100])
        self.upper_red2 = np.array([180, 255, 255])
        
        self.min_area = 500  # Minimum contour area

    def detect_dot(self, image: np.ndarray) -> bool:
        """
        Detect if a red dot/marker exists in the image.
        Args:
            image: BGR camera frame
        Returns:
            True if a red dot is found, False otherwise
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Morphological operations to remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > self.min_area:
                return True
                
        return False
