#!/usr/bin/env python3
"""
Pi-only line follower for DPSI-LFR.

This controller removes the ESP/Arduino motor node and drives the L298N
directly from the Raspberry Pi 4B. It borrows the practical core of
OJASP_follower: bottom ROI vision, strict black-line segmentation, marker
detection, nonlinear PID, gap recovery, and deterministic marker actions.
"""

from __future__ import annotations

import argparse
import atexit
import curses
import json
import math
import os
import queue
import select
import signal
import sys
import threading
import time
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

cv2 = None
np = None


def load_vision_deps() -> Tuple[Any, Any]:
    """Load OpenCV/Numpy lazily so `dpsi-cli --help` works off-robot."""
    global cv2, np
    if cv2 is None or np is None:
        try:
            import cv2 as _cv2  # type: ignore
            import numpy as _np  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "OpenCV/Numpy are required for camera processing. Install "
                "`requirements_pi_only.txt` or run `python3 -m pip install -e .`."
            ) from exc
        cv2 = _cv2
        np = _np
    return cv2, np


# =============================================================================
# HARDWARE CONFIGURATION - PRESERVE OLD NODE 1 PINS
# =============================================================================

CONFIG: Dict[str, Any] = {
    "robot": {
        "track_width_mm": 140.0,
        "rear_caster_arc_mm": 180.0,
        "motors": "2x N20 600 RPM",
        "driver": "L298N",
        "power": "LM2596 buck converter",
    },
    "gpio_bcm": {
        # Existing Node 1 pins. Do not move these without rewiring.
        "red_led": 5,          # Physical pin 29
        "green_led": 6,        # Physical pin 31
        "buzzer_pwm": 13,      # Physical pin 33
        "i2c_sda": 2,          # Physical pin 3
        "i2c_scl": 3,          # Physical pin 5
        "legacy_uart_tx": 14,  # Physical pin 8, retained for compatibility
        "legacy_uart_rx": 15,  # Physical pin 10, retained for compatibility

        # New direct Pi -> L298N motor pins. These avoid the old Node 1 pins.
        "left_ena_pwm": 12,    # Physical pin 32
        "left_in1": 16,        # Physical pin 36
        "left_in2": 20,        # Physical pin 38
        "right_ena_pwm": 18,   # Physical pin 12
        "right_in3": 21,       # Physical pin 40
        "right_in4": 26,       # Physical pin 37
    },
    "motor": {
        "pwm_frequency_hz": 1000,
        "left_invert": False,
        "right_invert": False,
        "deadband": 0.04,
        "slew_rate_per_sec": 5.0,
    },
    "camera": {
        "width": 320,
        "height": 240,
        "fps": 120,
        "roi_y_start_ratio": 0.48,
        "roi_x_start_ratio": 0.05,
        "roi_x_end_ratio": 0.95,
        "black_threshold": 82,
        "min_line_area": 45,
        "green_min_area": 80,
        "green_max_area": 5000,
        "red_min_area": 120,
        "center_importance_strength": 0.62,
        "branch_min_length": 22,
        # Camera mounting recommendation for the current robot:
        # 18-25 degrees down from horizontal, lens 85-120 mm above the mat,
        # with the bottom of the image seeing about 60-90 mm in front of the
        # drive axle. Start at 22 degrees and tune the ROI before changing code.
        "recommended_mount_angle_deg": 22,
    },
    "imu": {
        "enabled": True,
        "address": 0x68,
        "gyro_z_lsb_per_dps": 131.0,
        "max_reliable_dps": 400.0,
    },
}


# =============================================================================
# TUNABLES
# =============================================================================


@dataclass
class Tunables:
    kp: float = 0.85
    ki: float = 0.00
    kd: float = 0.18
    nonlinear_exponent: float = 1.35
    base_speed: float = 0.42
    max_speed: float = 0.82
    min_speed: float = 0.22
    turn_limit: float = 0.62
    speed_error_gain: float = 0.55
    integral_limit: float = 0.75
    gap_straight_time_s: float = 0.28
    gap_sweep_speed: float = 0.34
    gap_heading_gain: float = 0.018
    marker_debounce_s: float = 1.2
    turn_forward_time_s: float = 0.16
    turn_90_time_s: float = 0.48
    turn_speed: float = 0.48
    red_stop_enabled: bool = True
    # Annexure/preliminary mode: green dot blinks green LED and continues.
    # Final mode: green marker positions trigger LEFT/RIGHT/U_TURN decisions.
    marker_mode: str = "prelim"
    green_turns_enabled: bool = False


@dataclass
class Telemetry:
    running: bool = True
    paused: bool = False
    state: str = "BOOT"
    fps: float = 0.0
    loop_hz: float = 0.0
    line_seen: bool = False
    sensor_states: str = "0000000"
    error: float = 0.0
    pid_output: float = 0.0
    left_pwm: float = 0.0
    right_pwm: float = 0.0
    imu_heading_deg: Optional[float] = None
    imu_ok: bool = False
    marker: str = "NONE"
    line_candidate_count: int = 0
    intersection_branch_count: int = 0
    last_message: str = ""
    frame_shape: Tuple[int, int] = (0, 0)
    tunables_snapshot: Tunables = field(default_factory=Tunables)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def default_tuning_path() -> Path:
    return Path.home() / ".config" / "dpsi-lfr" / "tunables.json"


def load_tunables(path: Path, tunables: Tunables) -> bool:
    if not path.exists():
        return False
    allowed = {item.name for item in fields(Tunables)}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("tuning file must contain a JSON object")
    for key, value in payload.items():
        if key in allowed:
            setattr(tunables, key, value)
    return True


def save_tunables(path: Path, tunables: Tunables) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(tunables), handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_json_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


# =============================================================================
# HARDWARE
# =============================================================================


class Buzzer:
    def __init__(self, gpio: Any, pin: int, enabled: bool):
        self.gpio = gpio
        self.pin = pin
        self.enabled = enabled
        self._queue: "queue.Queue[List[Tuple[int, float]]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pwm = None
        if self.enabled:
            self.gpio.setup(self.pin, self.gpio.OUT)
            self._pwm = self.gpio.PWM(self.pin, 1000)
            self._pwm.start(0)
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def pattern(self, name: str) -> None:
        patterns = {
            "boot": [(1200, 0.08), (0, 0.05), (1600, 0.08)],
            "armed": [(1800, 0.06), (2200, 0.06)],
            "pause": [(700, 0.12)],
            "gap": [(900, 0.04), (0, 0.03), (900, 0.04)],
            "green": [(1400, 0.05), (0, 0.03), (1900, 0.08)],
            "red": [(500, 0.18), (0, 0.08), (500, 0.18)],
            "turn": [(1500, 0.04), (0, 0.02), (1500, 0.04), (0, 0.02), (1500, 0.04)],
            "error": [(350, 0.25)],
            "stop": [(2200, 0.05), (0, 0.04), (900, 0.12)],
        }
        if self.enabled and name in patterns:
            try:
                self._queue.put_nowait(patterns[name])
            except queue.Full:
                pass

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                pattern = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            for freq, duration in pattern:
                if self._stop.is_set():
                    break
                if freq <= 0:
                    if self._pwm:
                        self._pwm.ChangeDutyCycle(0)
                else:
                    if self._pwm:
                        self._pwm.ChangeFrequency(freq)
                        self._pwm.ChangeDutyCycle(35)
                time.sleep(duration)
            if self._pwm:
                self._pwm.ChangeDutyCycle(0)

    def close(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.4)
        if self._pwm:
            self._pwm.ChangeDutyCycle(0)
            self._pwm.stop()


class MotorDriver:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.gpio = None
        self.available = False
        self.left_pwm = None
        self.right_pwm = None
        self.last_left = 0.0
        self.last_right = 0.0
        self.last_update = time.perf_counter()
        self.buzzer: Optional[Buzzer] = None
        self.red_pin = CONFIG["gpio_bcm"]["red_led"]
        self.green_pin = CONFIG["gpio_bcm"]["green_led"]

        if not dry_run:
            try:
                import RPi.GPIO as GPIO  # type: ignore
                self.gpio = GPIO
                self.available = True
            except Exception as exc:
                print(f"[GPIO] RPi.GPIO unavailable, dry-run motors: {exc}")

        if self.available:
            g = self.gpio
            pins = CONFIG["gpio_bcm"]
            g.setmode(g.BCM)
            g.setwarnings(False)
            for key in ("left_in1", "left_in2", "right_in3", "right_in4", "red_led", "green_led"):
                g.setup(pins[key], g.OUT)
                g.output(pins[key], g.LOW)
            for key in ("left_ena_pwm", "right_ena_pwm"):
                g.setup(pins[key], g.OUT)
            self.left_pwm = g.PWM(pins["left_ena_pwm"], CONFIG["motor"]["pwm_frequency_hz"])
            self.right_pwm = g.PWM(pins["right_ena_pwm"], CONFIG["motor"]["pwm_frequency_hz"])
            self.left_pwm.start(0)
            self.right_pwm.start(0)
            self.buzzer = Buzzer(g, pins["buzzer_pwm"], enabled=True)
        else:
            self.buzzer = Buzzer(None, 0, enabled=False)

        atexit.register(self.close)

    def set_leds(self, red: bool = False, green: bool = False) -> None:
        if not self.available:
            return
        self.gpio.output(self.red_pin, self.gpio.HIGH if red else self.gpio.LOW)
        self.gpio.output(self.green_pin, self.gpio.HIGH if green else self.gpio.LOW)

    def _slew(self, target: float, previous: float, dt: float) -> float:
        step = CONFIG["motor"]["slew_rate_per_sec"] * max(0.001, dt)
        return clamp(target, previous - step, previous + step)

    def set_speeds(self, left: float, right: float) -> None:
        now = time.perf_counter()
        dt = now - self.last_update
        self.last_update = now

        if CONFIG["motor"]["left_invert"]:
            left = -left
        if CONFIG["motor"]["right_invert"]:
            right = -right

        left = self._slew(clamp(left, -1.0, 1.0), self.last_left, dt)
        right = self._slew(clamp(right, -1.0, 1.0), self.last_right, dt)
        self.last_left, self.last_right = left, right

        if not self.available:
            return

        self._apply_one(
            left,
            CONFIG["gpio_bcm"]["left_in1"],
            CONFIG["gpio_bcm"]["left_in2"],
            self.left_pwm,
        )
        self._apply_one(
            right,
            CONFIG["gpio_bcm"]["right_in3"],
            CONFIG["gpio_bcm"]["right_in4"],
            self.right_pwm,
        )

    def _apply_one(self, speed: float, pin_a: int, pin_b: int, pwm: Any) -> None:
        if abs(speed) < CONFIG["motor"]["deadband"]:
            self.gpio.output(pin_a, self.gpio.LOW)
            self.gpio.output(pin_b, self.gpio.LOW)
            pwm.ChangeDutyCycle(0)
            return
        if speed > 0:
            self.gpio.output(pin_a, self.gpio.HIGH)
            self.gpio.output(pin_b, self.gpio.LOW)
        else:
            self.gpio.output(pin_a, self.gpio.LOW)
            self.gpio.output(pin_b, self.gpio.HIGH)
        pwm.ChangeDutyCycle(abs(speed) * 100.0)

    def stop(self) -> None:
        self.set_speeds(0.0, 0.0)

    def close(self) -> None:
        try:
            self.stop()
            self.set_leds(False, False)
            if self.buzzer:
                self.buzzer.close()
            if self.left_pwm:
                self.left_pwm.stop()
            if self.right_pwm:
                self.right_pwm.stop()
            if self.available:
                self.gpio.cleanup()
        except Exception:
            pass


class MPU6050:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and CONFIG["imu"]["enabled"]
        self.available = False
        self.heading_deg = 0.0
        self._last_time = time.perf_counter()
        self._bus = None
        self._addr = CONFIG["imu"]["address"]
        if not self.enabled:
            return
        try:
            try:
                from smbus2 import SMBus  # type: ignore
            except Exception:
                from smbus import SMBus  # type: ignore
            self._bus = SMBus(1)
            self._bus.write_byte_data(self._addr, 0x6B, 0x00)
            self.available = True
        except Exception as exc:
            print(f"[IMU] MPU6050 unavailable, continuing without it: {exc}")

    def _read_word_signed(self, reg: int) -> int:
        high = self._bus.read_byte_data(self._addr, reg)
        low = self._bus.read_byte_data(self._addr, reg + 1)
        value = (high << 8) + low
        if value >= 0x8000:
            value = -((65535 - value) + 1)
        return value

    def update(self) -> Tuple[Optional[float], bool]:
        if not self.available:
            return None, False
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        try:
            gz_raw = self._read_word_signed(0x47)
            gz_dps = gz_raw / CONFIG["imu"]["gyro_z_lsb_per_dps"]
            if abs(gz_dps) <= CONFIG["imu"]["max_reliable_dps"]:
                self.heading_deg = (self.heading_deg + gz_dps * dt + 180.0) % 360.0 - 180.0
            return self.heading_deg, True
        except Exception as exc:
            self.available = False
            print(f"[IMU] read failed, disabling IMU fallback: {exc}")
            return None, False


# =============================================================================
# CAMERA AND VISION
# =============================================================================


class CameraSource:
    def __init__(self, camera_index: int = 0):
        load_vision_deps()
        self.picam2 = None
        self.cap = None
        self.use_picamera = False
        width = CONFIG["camera"]["width"]
        height = CONFIG["camera"]["height"]
        fps = CONFIG["camera"]["fps"]
        try:
            from picamera2 import Picamera2  # type: ignore
            self.picam2 = Picamera2()
            cfg = self.picam2.create_video_configuration(
                main={"size": (width, height), "format": "RGB888"},
                controls={"FrameRate": fps},
            )
            self.picam2.configure(cfg)
            self.picam2.start()
            self.use_picamera = True
            time.sleep(0.2)
        except Exception as exc:
            print(f"[Camera] Picamera2 unavailable, using cv2.VideoCapture({camera_index}): {exc}")
            self.cap = cv2.VideoCapture(camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

    def read(self) -> Optional[np.ndarray]:
        if self.use_picamera and self.picam2 is not None:
            rgb = self.picam2.capture_array()
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        if self.cap is not None:
            ok, frame = self.cap.read()
            return frame if ok else None
        return None

    def close(self) -> None:
        if self.picam2 is not None:
            self.picam2.stop()
        if self.cap is not None:
            self.cap.release()


@dataclass
class LineCandidate:
    center_x: int
    center_y: int
    area: float
    score: float
    angle_deg: float
    bbox: Tuple[int, int, int, int]


@dataclass
class VisionResult:
    line_seen: bool = False
    error: float = 0.0
    line_center_x: Optional[int] = None
    line_center_y: Optional[int] = None
    heading_vector: Tuple[float, float] = (0.0, -1.0)
    sensor_states: str = "0000000"
    special_state: str = "gap"
    green_left: bool = False
    green_right: bool = False
    red_stop: bool = False
    intersection: bool = False
    intersection_branch_count: int = 0
    line_candidates: List[LineCandidate] = field(default_factory=list)
    debug_frame: Optional[np.ndarray] = None
    mask_black: Optional[np.ndarray] = None


class VisionProcessor:
    def __init__(self):
        load_vision_deps()
        cam = CONFIG["camera"]
        self.green_lower = np.array([35, 80, 70])
        self.green_upper = np.array([90, 255, 255])
        self.red_lower_1 = np.array([0, 90, 80])
        self.red_upper_1 = np.array([10, 255, 255])
        self.red_lower_2 = np.array([165, 90, 80])
        self.red_upper_2 = np.array([180, 255, 255])
        self.black_threshold = cam["black_threshold"]

    def process(self, frame: np.ndarray, draw_debug: bool = False) -> VisionResult:
        h, w = frame.shape[:2]
        cam = CONFIG["camera"]
        y0 = int(h * cam["roi_y_start_ratio"])
        x0 = int(w * cam["roi_x_start_ratio"])
        x1 = int(w * cam["roi_x_end_ratio"])
        roi = frame[y0:h, x0:x1]
        roi_h, roi_w = roi.shape[:2]
        debug = frame.copy() if draw_debug else None

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        red_mask = cv2.bitwise_or(
            cv2.inRange(hsv, self.red_lower_1, self.red_upper_1),
            cv2.inRange(hsv, self.red_lower_2, self.red_upper_2),
        )

        kernel5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel5)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel5)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel5)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel5)

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, black_mask = cv2.threshold(blur, self.black_threshold, 255, cv2.THRESH_BINARY_INV)
        black_mask[green_mask > 0] = 0
        black_mask[red_mask > 0] = 0
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        black_closed = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

        result = VisionResult(debug_frame=debug, mask_black=black_closed)
        result.sensor_states = self._sensor_string(black_closed)
        center_x_global = x0 + roi_w // 2
        importance = self._importance_gradient(roi_h, roi_w)
        candidates = self._rank_line_candidates(black_closed, importance)
        result.line_candidates = [candidate for _, candidate in candidates]
        result.intersection_branch_count = self._count_line_branches(black_closed)
        line_contour = candidates[0][0] if candidates else None

        if line_contour is not None:
            M = cv2.moments(line_contour)
            if M["m00"] > 0:
                cx_roi = int(M["m10"] / M["m00"])
                cy_roi = int(M["m01"] / M["m00"])
                result.line_seen = True
                result.line_center_x = cx_roi + x0
                result.line_center_y = cy_roi + y0
                result.error = (result.line_center_x - center_x_global) / max(1.0, roi_w / 2.0)
                result.special_state = "line"

                shifted = line_contour + np.array([x0, y0])
                if len(shifted) >= 2:
                    vx, vy, _, _ = cv2.fitLine(shifted, cv2.DIST_L2, 0, 0.01, 0.01)
                    vx_f = float(vx.item())
                    vy_f = float(vy.item())
                    if vy_f > 0:
                        vx_f, vy_f = -vx_f, -vy_f
                    result.heading_vector = (vx_f, vy_f)

                bbox_x, _, bbox_w, _ = cv2.boundingRect(line_contour)
                result.intersection = (
                    bbox_w > roi_w * 0.70
                    or result.sensor_states.count("1") >= 5
                    or result.intersection_branch_count >= 3
                    or len(result.line_candidates) >= 2
                )
                if result.intersection:
                    result.special_state = "intersection"

                if draw_debug and debug is not None:
                    cv2.drawContours(debug, [shifted], -1, (255, 120, 0), 2)
                    cv2.circle(debug, (result.line_center_x, result.line_center_y), 5, (0, 0, 255), -1)
                    cv2.line(debug, (center_x_global, y0), (center_x_global, h), (255, 0, 0), 1)
                    for candidate in result.line_candidates[:4]:
                        x, y, bw, bh = candidate.bbox
                        cv2.rectangle(debug, (x + x0, y + y0), (x + x0 + bw, y + y0 + bh), (180, 180, 0), 1)
        else:
            result.special_state = "gap"
            if result.intersection_branch_count >= 2:
                result.intersection = True
                result.special_state = "intersection"

        result.green_left, result.green_right = self._detect_green(green_mask, x0, center_x_global, debug)
        result.red_stop = self._detect_red(red_mask, debug, x0, y0)
        if result.red_stop:
            result.special_state = "red"
        elif result.green_left or result.green_right:
            if result.green_left and result.green_right:
                result.special_state = "green_both"
            elif result.green_left:
                result.special_state = "green_left"
            else:
                result.special_state = "green_right"

        if draw_debug and debug is not None:
            cv2.rectangle(debug, (x0, y0), (x1, h), (0, 255, 255), 1)
            cv2.putText(
                debug,
                f"{result.special_state} branches:{result.intersection_branch_count} candidates:{len(result.line_candidates)}",
                (8, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 0),
                2,
            )
        return result

    def _sensor_string(self, mask: np.ndarray, zones: int = 7) -> str:
        h, w = mask.shape[:2]
        band = mask[int(h * 0.35):h, :]
        chars = []
        for i in range(zones):
            x0 = int(w * i / zones)
            x1 = int(w * (i + 1) / zones)
            density = float(np.count_nonzero(band[:, x0:x1])) / max(1, band[:, x0:x1].size)
            chars.append("1" if density > 0.035 else "0")
        return "".join(chars)

    def _importance_gradient(self, height: int, width: int) -> np.ndarray:
        strength = CONFIG["camera"]["center_importance_strength"]
        xs = np.linspace(-1.0, 1.0, width, dtype=np.float32)
        center_weight = 1.0 - strength * np.abs(xs)
        center_weight = np.clip(center_weight, 1.0 - strength, 1.0)

        # Slightly favor the lower/near part of the ROI while keeping center bias dominant.
        ys = np.linspace(0.78, 1.08, height, dtype=np.float32)
        return ys[:, None] * center_weight[None, :]

    def _rank_line_candidates(self, mask: np.ndarray, importance: np.ndarray) -> List[Tuple[np.ndarray, LineCandidate]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ranked: List[Tuple[np.ndarray, LineCandidate]] = []
        roi_center_x = mask.shape[1] / 2.0
        for c in contours:
            area = cv2.contourArea(c)
            if area < CONFIG["camera"]["min_line_area"]:
                continue
            rect = cv2.minAreaRect(c)
            rw, rh = rect[1]
            if rw <= 0 or rh <= 0:
                continue
            min_dim = min(rw, rh)
            max_dim = max(rw, rh)
            max_reasonable_line_width = max(58.0, min(mask.shape[:2]) * 0.75)
            if not (2 <= min_dim <= max_reasonable_line_width and max_dim >= 8):
                continue

            M = cv2.moments(c)
            if M["m00"] <= 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            x, y, bw, bh = cv2.boundingRect(c)
            contour_mask = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(contour_mask, [c], -1, 255, -1)
            weighted_pixels = importance[contour_mask > 0]
            importance_mean = float(weighted_pixels.mean()) if weighted_pixels.size else 0.0
            centeredness = 1.0 - min(1.0, abs(cx - roi_center_x) / max(1.0, roi_center_x))
            score = area * (0.45 + importance_mean) * (0.65 + 0.35 * centeredness)
            angle = self._contour_angle_deg(c)
            candidate = LineCandidate(
                center_x=cx,
                center_y=cy,
                area=float(area),
                score=float(score),
                angle_deg=angle,
                bbox=(x, y, bw, bh),
            )
            ranked.append((c, candidate))

        ranked.sort(key=lambda item: item[1].score, reverse=True)
        return ranked

    def _find_line_contour(self, mask: np.ndarray) -> Optional[np.ndarray]:
        importance = self._importance_gradient(mask.shape[0], mask.shape[1])
        ranked = self._rank_line_candidates(mask, importance)
        return ranked[0][0] if ranked else None

    def _contour_angle_deg(self, contour: np.ndarray) -> float:
        if len(contour) < 2:
            return 0.0
        vx, vy, _, _ = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
        return float(math.degrees(math.atan2(float(vy.item()), float(vx.item()))))

    def _count_line_branches(self, mask: np.ndarray) -> int:
        min_len = CONFIG["camera"]["branch_min_length"]
        lines = cv2.HoughLinesP(
            mask,
            rho=1,
            theta=np.pi / 180,
            threshold=18,
            minLineLength=min_len,
            maxLineGap=9,
        )
        if lines is None:
            return 0

        angle_bins = set()
        for line in lines.reshape(-1, 4):
            x1, y1, x2, y2 = [int(v) for v in line]
            length = math.hypot(x2 - x1, y2 - y1)
            if length < min_len:
                continue
            angle = (math.degrees(math.atan2(y2 - y1, x2 - x1)) + 180.0) % 180.0
            angle_bins.add(int(round(angle / 18.0)) * 18)
        return len(angle_bins)

    def _detect_green(self, mask: np.ndarray, x_offset: int, line_x: int, debug: Optional[np.ndarray]) -> Tuple[bool, bool]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        left = False
        right = False
        for c in contours:
            area = cv2.contourArea(c)
            if not (CONFIG["camera"]["green_min_area"] <= area <= CONFIG["camera"]["green_max_area"]):
                continue
            x, y, bw, bh = cv2.boundingRect(c)
            aspect = bw / max(1, bh)
            if not (0.35 <= aspect <= 2.4):
                continue
            cx = x + bw // 2 + x_offset
            if cx < line_x - 18:
                left = True
            elif cx > line_x + 18:
                right = True
            if debug is not None:
                cv2.rectangle(debug, (x + x_offset, y), (x + x_offset + bw, y + bh), (0, 255, 0), 2)
        return left, right

    def _detect_red(self, mask: np.ndarray, debug: Optional[np.ndarray], x_offset: int, y_offset: int) -> bool:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < CONFIG["camera"]["red_min_area"]:
                continue
            x, y, bw, bh = cv2.boundingRect(c)
            if debug is not None:
                cv2.rectangle(debug, (x + x_offset, y + y_offset), (x + x_offset + bw, y + y_offset + bh), (0, 0, 255), 2)
            return True
        return False


# =============================================================================
# NAVIGATION
# =============================================================================


class Navigator:
    def __init__(self, tunables: Tunables, motor: MotorDriver):
        self.t = tunables
        self.motor = motor
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.perf_counter()
        self.last_seen_time = self.last_time
        self.last_marker_time = 0.0
        self.state = "FOLLOW"
        self.turn_kind = "NONE"
        self.turn_start = 0.0
        self.turn_target_deg = 0.0
        self.turn_initial_heading: Optional[float] = None
        self.gap_initial_heading: Optional[float] = None

    def update(self, vision: VisionResult, heading_deg: Optional[float], paused: bool = False) -> Tuple[float, float, str, float]:
        now = time.perf_counter()
        dt = max(0.001, now - self.last_time)
        self.last_time = now

        if paused:
            self.motor.stop()
            return 0.0, 0.0, "PAUSED", 0.0

        if vision.red_stop and self.t.red_stop_enabled:
            self.state = "STOP_RED"
            self.motor.set_leds(red=True, green=False)
            if self.motor.buzzer:
                self.motor.buzzer.pattern("red")
            self.motor.stop()
            return 0.0, 0.0, "STOP_RED", 0.0

        marker = self._green_decision(vision)
        if marker != "NONE" and now - self.last_marker_time > self.t.marker_debounce_s:
            self.last_marker_time = now
            self.motor.set_leds(red=False, green=True)
            if self.motor.buzzer:
                self.motor.buzzer.pattern("green")
            if self.t.marker_mode == "final" and self.t.green_turns_enabled:
                self._start_turn(marker, heading_deg)

        if self.state == "TURN":
            left, right, state = self._handle_turn(heading_deg)
            self.motor.set_speeds(left, right)
            return left, right, state, 0.0

        if self.state == "STOP_RED":
            self.motor.stop()
            return 0.0, 0.0, "STOP_RED", 0.0

        if not vision.line_seen:
            left, right, state = self._handle_gap(now, heading_deg)
            self.motor.set_speeds(left, right)
            return left, right, state, 0.0

        self.state = "FOLLOW"
        self.last_seen_time = now
        self.gap_initial_heading = None
        self.motor.set_leds(red=False, green=False)

        error = clamp(vision.error, -1.0, 1.0)
        sign = 1.0 if error >= 0 else -1.0
        p_error = sign * (abs(error) ** self.t.nonlinear_exponent)
        self.integral = clamp(self.integral + error * dt, -self.t.integral_limit, self.t.integral_limit)
        derivative = (error - self.last_error) / dt
        self.last_error = error

        turn = (self.t.kp * p_error) + (self.t.ki * self.integral) + (self.t.kd * derivative)
        turn = clamp(turn, -self.t.turn_limit, self.t.turn_limit)
        speed = self.t.base_speed + (self.t.max_speed - self.t.base_speed) * max(0.0, 1.0 - abs(error) * 1.35)
        speed -= self.t.speed_error_gain * abs(error)
        speed = clamp(speed, self.t.min_speed, self.t.max_speed)

        left = clamp(speed + turn, -self.t.max_speed, self.t.max_speed)
        right = clamp(speed - turn, -self.t.max_speed, self.t.max_speed)
        self.motor.set_speeds(left, right)
        return left, right, "FOLLOW", turn

    def _green_decision(self, vision: VisionResult) -> str:
        if vision.green_left and vision.green_right:
            return "U_TURN"
        if vision.green_left:
            return "LEFT"
        if vision.green_right:
            return "RIGHT"
        return "NONE"

    def _start_turn(self, marker: str, heading_deg: Optional[float]) -> None:
        self.state = "TURN"
        self.turn_kind = marker
        self.turn_start = time.perf_counter()
        self.turn_initial_heading = heading_deg
        self.turn_target_deg = 180.0 if marker == "U_TURN" else 90.0
        if self.motor.buzzer:
            self.motor.buzzer.pattern("turn")

    def _handle_turn(self, heading_deg: Optional[float]) -> Tuple[float, float, str]:
        elapsed = time.perf_counter() - self.turn_start
        if elapsed < self.t.turn_forward_time_s:
            return self.t.min_speed, self.t.min_speed, f"TURN_{self.turn_kind}_SETTLE"

        turn_elapsed = elapsed - self.t.turn_forward_time_s
        timeout = self.t.turn_90_time_s * (2.0 if self.turn_kind == "U_TURN" else 1.0)
        if heading_deg is not None and self.turn_initial_heading is not None:
            delta = abs((heading_deg - self.turn_initial_heading + 180.0) % 360.0 - 180.0)
            if delta >= self.turn_target_deg * 0.86:
                self.state = "GAP"
                return self.t.gap_sweep_speed, self.t.gap_sweep_speed, "TURN_DONE"
        elif turn_elapsed >= timeout:
            self.state = "GAP"
            return self.t.gap_sweep_speed, self.t.gap_sweep_speed, "TURN_DONE"

        if self.turn_kind == "LEFT":
            return -self.t.turn_speed, self.t.turn_speed, "TURN_LEFT"
        if self.turn_kind == "RIGHT":
            return self.t.turn_speed, -self.t.turn_speed, "TURN_RIGHT"
        return self.t.turn_speed, -self.t.turn_speed, "TURN_U"

    def _handle_gap(self, now: float, heading_deg: Optional[float]) -> Tuple[float, float, str]:
        elapsed = now - self.last_seen_time
        if self.gap_initial_heading is None:
            self.gap_initial_heading = heading_deg
            if self.motor.buzzer:
                self.motor.buzzer.pattern("gap")

        if elapsed < self.t.gap_straight_time_s:
            correction = 0.0
            if heading_deg is not None and self.gap_initial_heading is not None:
                yaw_error = (heading_deg - self.gap_initial_heading + 180.0) % 360.0 - 180.0
                correction = clamp(yaw_error * self.t.gap_heading_gain, -0.18, 0.18)
            speed = clamp(self.t.base_speed * 0.72, self.t.min_speed, self.t.max_speed)
            return speed - correction, speed + correction, "GAP_STRAIGHT"

        direction = 1.0 if self.last_error >= 0 else -1.0
        return (
            self.t.gap_sweep_speed * direction,
            -self.t.gap_sweep_speed * direction,
            "GAP_SWEEP",
        )


# =============================================================================
# TUNING UI
# =============================================================================


class TuningInterface:
    def __init__(
        self,
        tunables: Tunables,
        telemetry: Telemetry,
        lock: threading.Lock,
        use_curses: bool,
        tuning_path: Path,
    ):
        self.t = tunables
        self.telemetry = telemetry
        self.lock = lock
        self.tuning_path = tuning_path
        self.use_curses = use_curses and sys.stdin.isatty() and sys.stdout.isatty()
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        target = self._curses_loop if self.use_curses else self._command_loop
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def _command_loop(self) -> None:
        print("[TUI] Non-interactive terminal detected. Commands: kp 0.9, ki 0, kd 0.2, base 0.4, max 0.8, save, load, pause, run, q")
        while self.telemetry.running:
            readable, _, _ = select.select([sys.stdin], [], [], 0.2)
            if not readable:
                continue
            line = sys.stdin.readline()
            if not line:
                continue
            self._apply_command(line.strip())

    def _curses_loop(self) -> None:
        curses.wrapper(self._curses_main)

    def _curses_main(self, stdscr: Any) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(100)
        while self.telemetry.running:
            key = stdscr.getch()
            if key != -1:
                self._handle_key(key)
            with self.lock:
                tel = Telemetry(**self.telemetry.__dict__)
            stdscr.erase()
            stdscr.addstr(0, 0, "DPSI-LFR Pi-only Line Follower TUI")
            stdscr.addstr(2, 0, f"State: {tel.state}  Paused: {tel.paused}  Loop: {tel.loop_hz:6.1f} Hz  FPS: {tel.fps:5.1f}")
            stdscr.addstr(3, 0, f"Sensors: {tel.sensor_states}  Line: {tel.line_seen}  Marker: {tel.marker}")
            stdscr.addstr(4, 0, f"Branches: {tel.intersection_branch_count}  Candidates: {tel.line_candidate_count}")
            stdscr.addstr(5, 0, f"Error: {tel.error:+.3f}  PID: {tel.pid_output:+.3f}  PWM L/R: {tel.left_pwm:+.3f}/{tel.right_pwm:+.3f}")
            imu = "None" if tel.imu_heading_deg is None else f"{tel.imu_heading_deg:+.1f} deg"
            stdscr.addstr(6, 0, f"IMU: {imu}  OK: {tel.imu_ok}")
            t = tel.tunables_snapshot
            stdscr.addstr(8, 0, f"Kp z/x: {t.kp:.4f}  Ki a/s: {t.ki:.5f}  Kd c/v: {t.kd:.4f}")
            stdscr.addstr(9, 0, f"Base [/]: {t.base_speed:.3f}  Max -/+: {t.max_speed:.3f}  Min: {t.min_speed:.3f}")
            stdscr.addstr(10, 0, f"Mode m: {t.marker_mode}  Green turns: {t.green_turns_enabled}  Red stop: {t.red_stop_enabled}")
            stdscr.addstr(11, 0, "Keys: space pause/run | q quit | w save | l load | m prelim/final | g green turns | r red stop")
            stdscr.addstr(12, 0, f"Tuning file: {self.tuning_path}")
            stdscr.addstr(13, 0, tel.last_message[:100])
            stdscr.refresh()

    def _handle_key(self, key: int) -> None:
        ch = chr(key) if 0 <= key < 256 else ""
        if ch == "q":
            self.telemetry.running = False
        elif ch == " ":
            self.telemetry.paused = not self.telemetry.paused
        elif ch == "z":
            self.t.kp = max(0.0, self.t.kp - 0.02)
        elif ch == "x":
            self.t.kp += 0.02
        elif ch == "a":
            self.t.ki = max(0.0, self.t.ki - 0.001)
        elif ch == "s":
            self.t.ki += 0.001
        elif ch == "c":
            self.t.kd = max(0.0, self.t.kd - 0.01)
        elif ch == "v":
            self.t.kd += 0.01
        elif ch == "[":
            self.t.base_speed = max(0.0, self.t.base_speed - 0.02)
        elif ch == "]":
            self.t.base_speed = min(1.0, self.t.base_speed + 0.02)
        elif ch == "-":
            self.t.max_speed = max(self.t.min_speed, self.t.max_speed - 0.02)
        elif ch == "+" or ch == "=":
            self.t.max_speed = min(1.0, self.t.max_speed + 0.02)
        elif ch == "g":
            self.t.green_turns_enabled = not self.t.green_turns_enabled
        elif ch == "r":
            self.t.red_stop_enabled = not self.t.red_stop_enabled
        elif ch == "m":
            self.t.marker_mode = "final" if self.t.marker_mode == "prelim" else "prelim"
            self.t.green_turns_enabled = self.t.marker_mode == "final"
        elif ch == "w":
            self._save_current()
        elif ch == "l":
            self._load_current()

    def _apply_command(self, line: str) -> None:
        if not line:
            return
        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd in ("q", "quit", "exit"):
                self.telemetry.running = False
            elif cmd == "pause":
                self.telemetry.paused = True
            elif cmd == "run":
                self.telemetry.paused = False
            elif cmd in ("kp", "ki", "kd", "base", "max", "min") and len(parts) == 2:
                value = float(parts[1])
                attr = {"kp": "kp", "ki": "ki", "kd": "kd", "base": "base_speed", "max": "max_speed", "min": "min_speed"}[cmd]
                setattr(self.t, attr, value)
            elif cmd == "green" and len(parts) == 2:
                self.t.green_turns_enabled = parts[1].lower() in ("1", "on", "true", "yes")
            elif cmd == "red" and len(parts) == 2:
                self.t.red_stop_enabled = parts[1].lower() in ("1", "on", "true", "yes")
            elif cmd == "mode" and len(parts) == 2:
                mode = parts[1].lower()
                if mode not in ("prelim", "final"):
                    print("[TUI] mode must be prelim or final")
                    return
                self.t.marker_mode = mode
                self.t.green_turns_enabled = mode == "final"
            elif cmd == "save":
                path = Path(parts[1]).expanduser() if len(parts) == 2 else self.tuning_path
                self._save_current(path)
            elif cmd == "load":
                path = Path(parts[1]).expanduser() if len(parts) == 2 else self.tuning_path
                self._load_current(path)
            else:
                print("[TUI] Unknown command")
        except ValueError:
            print("[TUI] Bad numeric value")

    def _save_current(self, path: Optional[Path] = None) -> None:
        target = path or self.tuning_path
        try:
            save_tunables(target, self.t)
            self.telemetry.last_message = f"Saved tuning to {target}"
            if not self.use_curses:
                print(f"[TUI] Saved tuning to {target}")
        except Exception as exc:
            self.telemetry.last_message = f"Save failed: {exc}"
            if not self.use_curses:
                print(f"[TUI] Save failed: {exc}")

    def _load_current(self, path: Optional[Path] = None) -> None:
        target = path or self.tuning_path
        try:
            loaded = load_tunables(target, self.t)
            if loaded:
                self.telemetry.last_message = f"Loaded tuning from {target}"
                if not self.use_curses:
                    print(f"[TUI] Loaded tuning from {target}")
            else:
                self.telemetry.last_message = f"No tuning file at {target}"
                if not self.use_curses:
                    print(f"[TUI] No tuning file at {target}")
        except Exception as exc:
            self.telemetry.last_message = f"Load failed: {exc}"
            if not self.use_curses:
                print(f"[TUI] Load failed: {exc}")


# =============================================================================
# MAIN LOOP
# =============================================================================


def run_self_test(args: argparse.Namespace) -> int:
    print("DPSI-LFR Pi-only hardware self-test")
    print(f"Mode: {args.mode}")
    print(f"Dry-run GPIO: {args.dry_run}")
    print(f"Motor pulse test: {args.motor_pulse_test}")

    status: List[Tuple[str, bool, str]] = []
    motor = MotorDriver(dry_run=args.dry_run)
    camera: Optional[CameraSource] = None

    try:
        status.append(("GPIO/L298N", args.dry_run or motor.available, "ready" if motor.available else "dry-run or unavailable"))

        if motor.available:
            motor.set_leds(red=True, green=False)
            if motor.buzzer:
                motor.buzzer.pattern("boot")
            time.sleep(0.15)
            motor.set_leds(red=False, green=True)
            time.sleep(0.15)
            motor.set_leds(red=False, green=False)
            status.append(("LED/Buzzer", True, "indicator pulse sent"))
        else:
            status.append(("LED/Buzzer", args.dry_run, "skipped without GPIO"))

        imu = MPU6050(enabled=not args.no_imu)
        heading, imu_ok = imu.update()
        if args.no_imu:
            status.append(("MPU6050", True, "disabled by --no-imu"))
        else:
            status.append(("MPU6050", imu_ok, f"heading={heading}" if imu_ok else "not available"))

        vision = VisionProcessor()
        camera = CameraSource(camera_index=args.camera_index)
        frame = None
        frame_count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < 1.0:
            candidate = camera.read()
            if candidate is not None:
                frame = candidate
                frame_count += 1
        if frame is None:
            status.append(("Camera", False, "no frames captured"))
        else:
            result = vision.process(frame, draw_debug=False)
            status.append(("Camera", True, f"{frame_count} frames in 1.0s, shape={frame.shape[:2]}"))
            status.append(("Vision", True, f"line={result.line_seen} sensors={result.sensor_states} marker={result.special_state}"))

        if args.motor_pulse_test:
            if args.dry_run or not motor.available:
                status.append(("Motor pulse", False, "requires GPIO and no --dry-run"))
            else:
                print("Pulsing motors at low power. Robot must be lifted off the mat.")
                motor.set_speeds(0.24, 0.24)
                time.sleep(0.25)
                motor.set_speeds(-0.20, -0.20)
                time.sleep(0.18)
                motor.stop()
                status.append(("Motor pulse", True, "low-power forward/reverse pulse sent"))
        else:
            status.append(("Motor pulse", True, "skipped; add --motor-pulse-test when robot is lifted"))

    finally:
        motor.stop()
        if camera is not None:
            camera.close()
        motor.close()

    print("\nSelf-test results:")
    ok = True
    for name, passed, detail in status:
        ok = ok and passed
        label = "PASS" if passed else "WARN"
        print(f"[{label}] {name}: {detail}")
    if args.report_file:
        report = {
            "kind": "self-test",
            "ok": ok,
            "mode": args.mode,
            "dry_run": args.dry_run,
            "no_imu": args.no_imu,
            "motor_pulse_test": args.motor_pulse_test,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": [
                {"name": name, "passed": passed, "detail": detail}
                for name, passed, detail in status
            ],
        }
        target = Path(args.report_file).expanduser()
        write_json_report(target, report)
        print(f"Report written to {target}")
    return 0 if ok else 1


def _benchmark_frame(index: int) -> Any:
    cv2_mod, np_mod = load_vision_deps()
    width = CONFIG["camera"]["width"]
    height = CONFIG["camera"]["height"]
    frame = np_mod.full((height, width, 3), 255, dtype=np_mod.uint8)
    phase = index % 120
    line_x = int(width / 2 + math.sin(index / 13.0) * width * 0.22)
    if not 88 <= phase <= 96:
        cv2_mod.line(frame, (line_x, int(height * 0.45)), (line_x, height - 1), (0, 0, 0), 14)
    if phase == 30:
        cv2_mod.circle(frame, (max(20, line_x - 62), int(height * 0.80)), 13, (0, 180, 0), -1)
    elif phase == 60:
        cv2_mod.circle(frame, (min(width - 20, line_x + 62), int(height * 0.80)), 13, (0, 180, 0), -1)
    return frame


def run_benchmark(args: argparse.Namespace) -> int:
    frames = max(1, args.benchmark_frames)
    vision = VisionProcessor()
    motor = MotorDriver(dry_run=True)
    nav = Navigator(Tunables(), motor)
    generated = [_benchmark_frame(i) for i in range(min(frames, 240))]

    # Warm up OpenCV kernels and Python object paths before measuring.
    for frame in generated[: min(20, len(generated))]:
        result = vision.process(frame, draw_debug=False)
        nav.update(result, None)

    start = time.perf_counter()
    line_seen = 0
    marker_seen = 0
    for i in range(frames):
        frame = generated[i % len(generated)]
        result = vision.process(frame, draw_debug=False)
        nav.update(result, None)
        line_seen += 1 if result.line_seen else 0
        marker_seen += 1 if result.special_state not in ("line", "gap") else 0
    elapsed = max(0.000001, time.perf_counter() - start)
    hz = frames / elapsed
    motor.close()

    print("DPSI-LFR synthetic vision/navigation benchmark")
    print(f"Frames: {frames}")
    print(f"Elapsed: {elapsed:.4f}s")
    print(f"Loop rate: {hz:.1f} Hz")
    print(f"Line frames: {line_seen}/{frames}")
    print(f"Marker frames: {marker_seen}/{frames}")
    passed = hz >= 100.0
    if args.report_file:
        report = {
            "kind": "benchmark",
            "passed_100hz": passed,
            "frames": frames,
            "elapsed_s": elapsed,
            "loop_hz": hz,
            "line_frames": line_seen,
            "marker_frames": marker_seen,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        target = Path(args.report_file).expanduser()
        write_json_report(target, report)
        print(f"Report written to {target}")
    if hz < 100.0:
        print("WARN: below 100 Hz target on this machine; test on Pi with camera preview off.")
        return 1 if args.benchmark_require_100hz else 0
    print("PASS: above 100 Hz synthetic processing target")
    return 0


def run(args: argparse.Namespace) -> int:
    tunables = Tunables()
    tuning_path = Path(args.tuning_file).expanduser() if args.tuning_file else default_tuning_path()
    profile_message = f"Tuning file: {tuning_path}"
    try:
        if load_tunables(tuning_path, tunables):
            profile_message = f"Loaded tuning from {tuning_path}"
    except Exception as exc:
        profile_message = f"Tuning load failed: {exc}"

    tunables.marker_mode = args.mode
    tunables.green_turns_enabled = args.mode == "final"
    telemetry = Telemetry(last_message=profile_message)
    lock = threading.Lock()
    motor = MotorDriver(dry_run=args.dry_run)
    imu = MPU6050(enabled=not args.no_imu)
    vision = VisionProcessor()
    nav = Navigator(tunables, motor)
    camera = CameraSource(camera_index=args.camera_index)
    tui: Optional[TuningInterface] = None
    if not args.headless:
        tui = TuningInterface(tunables, telemetry, lock, use_curses=not args.no_tui, tuning_path=tuning_path)
        tui.start()

    if motor.buzzer:
        motor.buzzer.pattern("boot")

    def _signal_stop(signum: int, frame: Any) -> None:
        telemetry.running = False

    signal.signal(signal.SIGINT, _signal_stop)
    signal.signal(signal.SIGTERM, _signal_stop)

    last_loop = time.perf_counter()
    last_fps_time = last_loop
    frames = 0
    preview = args.preview and not args.no_tui

    try:
        while telemetry.running:
            start = time.perf_counter()
            frame = camera.read()
            if frame is None:
                with lock:
                    telemetry.state = "CAMERA_LOST"
                    telemetry.last_message = "No camera frame"
                motor.stop()
                time.sleep(0.02)
                continue

            heading, imu_ok = imu.update()
            result = vision.process(frame, draw_debug=preview)
            left, right, state, pid_output = nav.update(result, heading, telemetry.paused)

            frames += 1
            now = time.perf_counter()
            fps_window = now - last_fps_time
            if fps_window >= 0.5:
                fps = frames / fps_window
                frames = 0
                last_fps_time = now
            else:
                fps = telemetry.fps

            loop_dt = max(0.0001, now - last_loop)
            last_loop = now
            marker = result.special_state.upper()
            with lock:
                telemetry.state = state
                telemetry.fps = fps
                telemetry.loop_hz = 1.0 / loop_dt
                telemetry.line_seen = result.line_seen
                telemetry.sensor_states = result.sensor_states
                telemetry.error = result.error
                telemetry.pid_output = pid_output
                telemetry.left_pwm = left
                telemetry.right_pwm = right
                telemetry.imu_heading_deg = heading
                telemetry.imu_ok = imu_ok
                telemetry.marker = marker
                telemetry.line_candidate_count = len(result.line_candidates)
                telemetry.intersection_branch_count = result.intersection_branch_count
                telemetry.frame_shape = frame.shape[:2]
                telemetry.tunables_snapshot = Tunables(**tunables.__dict__)

            if preview:
                if result.debug_frame is not None:
                    cv2.imshow("DPSI-LFR Debug", result.debug_frame)
                if result.mask_black is not None:
                    cv2.imshow("Black Mask", result.mask_black)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    telemetry.running = False

            elapsed = time.perf_counter() - start
            if elapsed < 0.001:
                time.sleep(0.001 - elapsed)
    finally:
        telemetry.running = False
        if args.save_on_exit:
            try:
                save_tunables(tuning_path, tunables)
                print(f"[Tuning] Saved tuning to {tuning_path}")
            except Exception as exc:
                print(f"[Tuning] Save on exit failed: {exc}")
        motor.stop()
        if motor.buzzer:
            motor.buzzer.pattern("stop")
            time.sleep(0.25)
        motor.close()
        camera.close()
        if preview:
            cv2.destroyAllWindows()
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pi-only DPSI-LFR competition line follower")
    parser.add_argument("--mode", choices=("prelim", "final"), default="prelim",
                        help="prelim follows annexure green=blink/continue, red=stop; final enables green-marker turns")
    parser.add_argument("--dry-run", action="store_true", help="Run without GPIO motor output")
    parser.add_argument("--preview", action="store_true", help="Show OpenCV debug windows")
    parser.add_argument("--no-tui", action="store_true", help="Disable curses TUI and use command CLI only")
    parser.add_argument("--headless", action="store_true", help="Disable all interactive tuning UI; useful for systemd services")
    parser.add_argument("--no-imu", action="store_true", help="Disable MPU6050 reads")
    parser.add_argument("--camera-index", type=int, default=0, help="cv2 camera index if Picamera2 is unavailable")
    parser.add_argument("--tuning-file", help="JSON tuning profile path (default: ~/.config/dpsi-lfr/tunables.json)")
    parser.add_argument("--save-on-exit", action="store_true", help="Write current PID/speed settings to the tuning file on exit")
    parser.add_argument("--self-test", action="store_true", help="Check GPIO, camera, vision, and IMU without starting autonomous driving")
    parser.add_argument("--motor-pulse-test", action="store_true", help="During --self-test, briefly pulse motors at low power; lift robot first")
    parser.add_argument("--benchmark", action="store_true", help="Run synthetic no-GPIO vision/navigation loop benchmark")
    parser.add_argument("--benchmark-frames", type=int, default=1000, help="Number of frames for --benchmark")
    parser.add_argument("--benchmark-require-100hz", action="store_true", help="Make --benchmark fail if synthetic loop rate is below 100 Hz")
    parser.add_argument("--report-file", help="Write JSON report for --self-test or --benchmark")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.self_test:
        return run_self_test(args)
    if args.benchmark:
        return run_benchmark(args)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
