import cv2
import numpy as np

class VisionAgent:
    def __init__(self, resolution=(320, 240)):
        self.resolution = resolution
        # Try to initialize PiCamera, fallback to standard cv2 VideoCapture
        self.use_picamera = False
        try:
            from picamera.array import PiRGBArray
            from picamera import PiCamera
            self.camera = PiCamera()
            self.camera.resolution = self.resolution
            self.camera.framerate = 30
            self.rawCapture = PiRGBArray(self.camera, size=self.resolution)
            self.use_picamera = True
            # Let camera warmup
            import time
            time.sleep(0.1)
        except ImportError:
            print("picamera module not found, using cv2.VideoCapture(0) instead.")
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
    def get_frame(self):
        """Yields frames from the chosen camera."""
        if self.use_picamera:
            for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
                img = frame.array
                self.rawCapture.truncate(0)
                yield img
        else:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                yield frame

    def process_frame(self, frame):
        """
        Processes a single frame using the AlexNet-style multi-kernel filter bank.
        Returns a dict containing line position, obstacle info, markers, etc.
        """
        result = {
            "line_center_x": None,
            "line_center_y": None,
            "obstacle_detected": False,
            "obstacle_box": None,
            "special_state": None, # e.g., "intersection", "gap"
            "cnn_layers": None,
            "green_dot_detected": False,
            "red_dot_detected": False
        }
        
        h, w = frame.shape[:2]
        
        # 1. Preprocessing (Crop top half if only focusing on floor)
        roi_start_y = int(h/3)
        roi = frame[roi_start_y:, :] # Look at the bottom 2/3rds of the image
        roi_h = roi.shape[0]
        
        # Draw a yellow box on the main frame to indicate the exact ROI being used
        cv2.rectangle(frame, (0, roi_start_y), (w, h), (0, 255, 255), 2)
        cv2.putText(frame, "ROI (Yellow Box)", (10, roi_start_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # 2. Red Detection (Obstacles vs Stop Lines/Dots)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask_red_1 = cv2.inRange(hsv_roi, np.array([0, 120, 70]), np.array([10, 255, 255]))
        mask_red_2 = cv2.inRange(hsv_roi, np.array([170, 120, 70]), np.array([180, 255, 255]))
        mask_red = mask_red_1 + mask_red_2
        
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_red:
            largest_red = max(contours_red, key=cv2.contourArea)
            area = cv2.contourArea(largest_red)
            if area > 500: # Threshold for a valid object
                perimeter = cv2.arcLength(largest_red, True)
                circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
                
                x, y, w_box, h_box = cv2.boundingRect(largest_red)
                real_y = y + roi_start_y
                
                # Check aspect ratio: wide objects are lines, square objects are cubes
                aspect_ratio = float(w_box) / max(1, h_box)
                
                is_red_marker = (aspect_ratio > 3.0) or (circularity > 0.8 and 0.5 <= aspect_ratio <= 2.0)
                
                if is_red_marker: # Red Line/Dot
                    # Only trigger STOP if the marker is physically beneath the robot (bottom 25% of the frame)
                    if real_y > frame.shape[0] * 0.75:
                        result["special_state"] = "stop_line"
                        result["red_dot_detected"] = True
                        cv2.rectangle(frame, (x, real_y), (x + w_box, real_y + h_box), (0, 0, 255), -1) # Fill red
                        cv2.putText(frame, "RED STOP LINE/DOT (STOP)", (x, real_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    else:
                        # Marker is visible but still ahead, do not stop yet
                        cv2.rectangle(frame, (x, real_y), (x + w_box, real_y + h_box), (0, 0, 255), 2)
                        cv2.putText(frame, "Red Marker Ahead", (x, real_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else: # Red Cube (Obstacle)
                    result["obstacle_detected"] = True
                    result["obstacle_box"] = (x, real_y, w_box, h_box)
                    cv2.rectangle(frame, (x, real_y), (x + w_box, real_y + h_box), (0, 0, 255), 3)
                    cv2.putText(frame, "Obstacle Cube", (x, real_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 3. Green Dot Detection (Competition Rule)
        # Green color bounds in HSV
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv_roi, lower_green, upper_green)
        
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_green:
            largest_green = max(contours_green, key=cv2.contourArea)
            if cv2.contourArea(largest_green) > 200: # suitable area threshold
                gx, gy, gw, gh = cv2.boundingRect(largest_green)
                real_gy = gy + roi_start_y
                result["green_dot_detected"] = True
                cv2.rectangle(frame, (gx, real_gy), (gx + gw, real_gy + gh), (0, 255, 0), 2)
                cv2.putText(frame, "GREEN DOT DETECTED", (gx, real_gy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 4. Strictly Black Line Detection
        # Convert to grayscale and smooth to reduce high-frequency noise
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Paint the obstacle pixels out of the input so it doesn't track them
        blurred[mask_red > 0] = 255
        blurred[mask_green > 0] = 255
        
        # Use a strict Global Threshold to isolate the black line.
        # Any pixel darker than 80 becomes 255 (White in the mask).
        # Any pixel lighter than 80 (the white paper) becomes 0 (Black in the mask).
        _, mask_black = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological OPEN to remove tiny speckle noise
        kernel_open = np.ones((3, 3), np.uint8)
        mask_black = cv2.morphologyEx(mask_black, cv2.MORPH_OPEN, kernel_open)
        
        # Morphological CLOSE to bridge small gaps in the solid line block
        kernel_close = np.ones((9, 9), np.uint8)
        mask_closed = cv2.morphologyEx(mask_black, cv2.MORPH_CLOSE, kernel_close)
        
        result["cnn_layers"] = {
            "Black_Mask": mask_black,
            "Mask_Closed": mask_closed
        }
        
        # 5. Extract line position using Contours
        contours_line, _ = cv2.findContours(mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours_line:
            # Filter contours geometrically to match the exact ~10px width of the line
            valid_contours = []
            for c in contours_line:
                area = cv2.contourArea(c)
                if area < 50: # Lowered area floor since the line is much thinner now
                    continue
                    
                # Use minAreaRect to get the true physical width/height regardless of rotation
                rect = cv2.minAreaRect(c)
                rect_w, rect_h = rect[1]
                if rect_w == 0 or rect_h == 0:
                    continue
                    
                min_dim = min(rect_w, rect_h)
                max_dim = max(rect_w, rect_h)
                
                # Constraint: "10 pixels wide" (We allow 5 to 30 to account for camera blur/distance)
                if not (5 <= min_dim <= 30):
                    continue
                    
                valid_contours.append(c)
                
            if valid_contours:
                largest_line = max(valid_contours, key=cv2.contourArea)
                
                # Use geometric moments to find the center of gravity of the black line
                M = cv2.moments(largest_line)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"]) + roi_start_y
                    result["line_center_x"] = cx
                    result["line_center_y"] = cy
                    
                    shifted_contour = largest_line + np.array([0, roi_start_y])
                    
                    # Fit a line to the contour to calculate the directional heading vector
                    [vx, vy, x, y] = cv2.fitLine(shifted_contour, cv2.DIST_L2, 0, 0.01, 0.01)
                    
                    # Extracted values are 1D numpy arrays, unwrap them to scalar floats
                    vx = vx.item()
                    vy = vy.item()
                    
                    # Ensure the heading vector always points "forward" (up the screen, so negative Y)
                    if vy > 0:
                        vx = -vx
                        vy = -vy
                        
                    # Draw a fitted shape (Ellipse) around the line contour to highlight it
                    if len(shifted_contour) >= 5:
                        ellipse = cv2.fitEllipse(shifted_contour)
                        cv2.ellipse(frame, ellipse, (255, 100, 0), 2)
                    else:
                        cv2.drawContours(frame, [shifted_contour], -1, (255, 100, 0), 2)
                        
                    # Draw the heading vector arrow extending from the center of gravity
                    length = 70
                    pt1 = (cx, cy)
                    pt2 = (int(cx + vx * length), int(cy + vy * length))
                    cv2.arrowedLine(frame, pt1, pt2, (0, 255, 255), 4, tipLength=0.3)
                    
                    cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)
                    cv2.putText(frame, f"Vector Heading CX:{cx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
                    # Basic intersection detection
                    x_box, y_box, w_line, h_line = cv2.boundingRect(largest_line)
                    if w_line > w * 0.8: # Line edge takes up 80% of width
                        result["special_state"] = "intersection"
                        cv2.putText(frame, "INTERSECTION", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            else:
                result["special_state"] = "gap"
        else:
            result["special_state"] = "gap"
            
        return result
