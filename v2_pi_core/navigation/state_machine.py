import time
from typing import Optional
from comms.esp_bridge import ESPBridge
from vision.camera_warp import PerspectiveWarper
from vision.green_dot import GreenDotDetector
from vision.red_dot import RedDotDetector
import numpy as np

# ============================================================================
# NAVIGATION STATES
# ============================================================================
STATE_LINE_FOLLOWING = 0
STATE_INTERSECTION_DECISION = 1
STATE_OBSTACLE_AVOIDANCE = 2
STATE_RESCUE_ZONE_NAVIGATION = 3

# ESP32 Modes
MODE_STANDBY = 0
MODE_LINE_FOLLOW = 1
MODE_MANUAL = 2

# ============================================================================
# NAVIGATION MASTER FSM
# ============================================================================

class NavigationMaster:
    def __init__(self, esp_bridge: ESPBridge, warper: PerspectiveWarper,
                 green_detector: GreenDotDetector, red_detector: RedDotDetector = None):
        """
        Initialize navigation FSM controller.

        Args:
            esp_bridge: Serial communication bridge to ESP32
            warper: Perspective transformation handler
            green_detector: Green dot detection handler
        """
        self.esp = esp_bridge
        self.warper = warper
        self.green_detector = green_detector
        self.red_detector = red_detector if red_detector else RedDotDetector()

        self.state = STATE_LINE_FOLLOWING
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 0.2

        self.turn_issued = False
        self.turn_start_time = 0.0

        self.last_green_led_time = 0.0
        self.last_red_led_time = 0.0

    def start(self):
        """Start navigation by enabling line following mode."""
        self.esp.set_mode(MODE_LINE_FOLLOW)
        self.state = STATE_LINE_FOLLOWING
        print("Navigation started: LINE_FOLLOWING mode")

    def stop(self):
        """Stop navigation and return to standby."""
        self.esp.set_mode(MODE_STANDBY)
        self.esp.emergency_stop()
        print("Navigation stopped")

    def process_frame(self, frame: np.ndarray):
        """
        Process single camera frame and execute FSM logic.

        Args:
            frame: Raw camera frame
        """
        if time.time() - self.last_heartbeat >= self.heartbeat_interval:
            self.esp.send_heartbeat()
            self.last_heartbeat = time.time()

        warped = self.warper.warp(frame)
        
        if self.state == STATE_LINE_FOLLOWING:
            # 1. Check for Red Dot (Highest Priority)
            if self.red_detector.detect_dot(warped):
                if time.time() - self.last_red_led_time > 2.0:
                    print("RED DOT DETECTED! Stopping and blinking red LED.")
                    self.esp.action_red_led()
                    self.last_red_led_time = time.time()
                    self.stop()
                return

            # 2. Check for Green Dot
            dots = self.green_detector.detect_dots(warped)
            self._handle_line_following(dots)

        elif self.state == STATE_INTERSECTION_DECISION:
            self._handle_intersection_decision()

    def _handle_line_following(self, dots):
        """Handle line following state logic."""
        if len(dots) > 0:
            if time.time() - self.last_green_led_time > 2.0:
                print("GREEN DOT DETECTED! Blinking green LED.")
                self.esp.action_green_led()
                self.last_green_led_time = time.time()

            decision = self.green_detector.evaluate_intersection(dots, None)

            if decision != "NONE":
                print(f"Intersection detected: {decision}")
                self.state = STATE_INTERSECTION_DECISION

                if decision == "TURN_LEFT":
                    self.esp.execute_turn_90("LEFT")
                    self.turn_issued = True
                    self.turn_start_time = time.time()
                elif decision == "TURN_RIGHT":
                    self.esp.execute_turn_90("RIGHT")
                    self.turn_issued = True
                    self.turn_start_time = time.time()
                elif decision == "U_TURN":
                    self.esp.execute_turn_180()
                    self.turn_issued = True
                    self.turn_start_time = time.time()

    def _handle_intersection_decision(self):
        """Handle intersection decision state logic."""
        if self.turn_issued:
            if self.esp.check_turn_complete():
                print("Turn complete, resuming line following")
                self.turn_issued = False
                self.state = STATE_LINE_FOLLOWING
                self.esp.set_mode(MODE_LINE_FOLLOW)
            elif time.time() - self.turn_start_time > 5.0:
                print("Turn timeout, resuming line following")
                self.turn_issued = False
                self.state = STATE_LINE_FOLLOWING
                self.esp.set_mode(MODE_LINE_FOLLOW)
