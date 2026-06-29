import cv2
import numpy as np

# ============================================================================
# PERSPECTIVE WARPER CLASS
# ============================================================================

class PerspectiveWarper:
    def __init__(self, src_pts: np.ndarray, dst_pts: np.ndarray, output_size: tuple = (400, 400)):
        """
        Initialize perspective transformation matrix.

        Args:
            src_pts: Source points in original frame (4x2 array)
            dst_pts: Destination points in warped frame (4x2 array)
            output_size: Output frame dimensions (width, height)
        """
        self.M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        self.output_size = output_size

    def warp(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply perspective transformation to frame.

        Args:
            frame: Input frame from camera

        Returns:
            Rectified bird's-eye view frame
        """
        return cv2.warpPerspective(frame, self.M, self.output_size)
