from picamera2 import Picamera2
import cv2
import numpy as np

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None


# ---------------------------------------------------------------------------
# PID Controller
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
KP = 0.004
KI = 0.000
KD = 0.002

BASE_SPEED = 0.35
SERIAL_BAUD = 115200


def clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))


def open_serial():
    if serial is None:
        print("[Serial] pyserial not installed - running without serial output")
        return None
    for port in ("/dev/serial0", "/dev/ttyUSB0"):
        try:
            ser = serial.Serial(port, SERIAL_BAUD, timeout=1)
            print(f"[Serial] Connected on {port}")
            return ser
        except (OSError, serial.SerialException):
            continue
    print("[Serial] No serial port available - running without serial output")
    return None


def send_motor_command(ser, left_speed, right_speed):
    if ser is None:
        return
    cmd = f"M:{right_speed:.4f},{left_speed:.4f}\n"
    try:
        ser.write(cmd.encode("utf-8"))
    except (OSError, serial.SerialException) as e:
        print(f"[Serial] write error: {e}")


# ---------------------------------------------------------------------------
# Initialize camera
# ---------------------------------------------------------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)

picam2.configure(config)
picam2.start()

pid = PIDController(kp=KP, ki=KI, kd=KD)
ser = open_serial()

try:
    while True:
        frame = picam2.capture_array()

        # Flip if needed
        # frame = cv2.flip(frame, -1)

        # Use only the lower half of the image
        roi = frame[240:480, :]

        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)

        # Blur to remove noise
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Threshold (black line on white background)
        _, thresh = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            # Largest contour
            c = max(contours, key=cv2.contourArea)

            # Ignore tiny blobs
            if cv2.contourArea(c) > 500:

                M = cv2.moments(c)

                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # Draw contour
                    cv2.drawContours(roi, [c], -1, (0, 255, 0), 2)

                    # Draw center
                    cv2.circle(roi, (cx, cy), 5, (0, 0, 255), -1)

                    # Draw center line
                    cv2.line(roi, (cx, 0), (cx, roi.shape[0]), (255, 0, 0), 2)

                    # Steering error
                    error = cx - (roi.shape[1] // 2)

                    # PID steering adjustment
                    steering_adjustment = pid.compute(error)

                    left_speed = clamp(BASE_SPEED + steering_adjustment)
                    right_speed = clamp(BASE_SPEED - steering_adjustment)

                    send_motor_command(ser, left_speed, right_speed)

                    cv2.putText(
                        roi,
                        f"Error: {error}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 0),
                        2
                    )

                    cv2.putText(
                        roi,
                        f"L:{left_speed:.3f} R:{right_speed:.3f}",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2
                    )

                    print(f"Error: {error}  L: {left_speed:.4f}  R: {right_speed:.4f}")

        cv2.imshow("Line Tracking Preview", frame)
        cv2.imshow("Threshold", thresh)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    if ser is not None:
        try:
            ser.close()
        except Exception:
            pass
    picam2.stop()
    cv2.destroyAllWindows()
