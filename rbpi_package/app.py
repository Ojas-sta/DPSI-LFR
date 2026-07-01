import time
import cv2
import threading
import sys
import os
import curses

from hardware import RobotHardware
import cli

class PIDController:
    def __init__(self, kp=0.0, ki=0.0, kd=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._prev_error = 0.0
        self._integral = 0.0

    def reset(self):
        self._prev_error = 0.0
        self._integral = 0.0

    def compute(self, error, dt=1.0):
        self._integral += error * dt
        derivative = (error - self._prev_error) / dt if dt > 0 else 0.0
        self._prev_error = error
        return (self.kp * error) + (self.ki * self._integral) + (self.kd * derivative)

class SharedState:
    def __init__(self):
        self.mode = "MANUAL"
        self.armed = False
        self.running = True

def clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))

def vision_loop(hw, state):
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()
    except Exception as e:
        hw.log_telemetry(f"Camera init failed: {e}")
        return

    pid = PIDController(kp=0.004, ki=0.000, kd=0.002)
    BASE_SPEED = 0.35

    try:
        while state.running:
            try:
                frame = picam2.capture_array()
            except Exception:
                time.sleep(0.1)
                continue

            roi = frame[240:480, :]
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY_INV)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            error = 0
            if contours:
                c = max(contours, key=cv2.contourArea)
                if cv2.contourArea(c) > 500:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        error = cx - (roi.shape[1] // 2)
                        
                        if state.mode == "AUTO" and state.armed:
                            steering_adjustment = pid.compute(error)
                            left_speed = clamp(BASE_SPEED + steering_adjustment)
                            right_speed = clamp(BASE_SPEED - steering_adjustment)
                            hw.set_speeds(left_speed, right_speed)
                            hw.log_telemetry(f"AUTO: err={error} L={left_speed:.2f} R={right_speed:.2f}")

            # Do not use cv2.imshow in the background thread when curses is running in the main thread
            # as it causes display server conflicts. We run headlessly.
            time.sleep(0.02)
    finally:
        try:
            picam2.stop()
        except:
            pass

def main():
    hw = RobotHardware()
    state = SharedState()
    
    vt = threading.Thread(target=vision_loop, args=(hw, state), daemon=True)
    vt.start()
    
    # Launch the Curses TUI in the main thread
    curses.wrapper(lambda stdscr: cli.run_tui(stdscr, hw, state))

if __name__ == "__main__":
    main()
