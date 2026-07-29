#!/usr/bin/env python3
"""Synthetic smoke test for the Pi-only line follower.

This test does not touch GPIO or camera hardware. It generates simple
competition-mat-like frames and verifies vision + navigation decisions.
"""

import cv2
import numpy as np
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rpi_line_follower.pi_only_follower import (
    ExpertWorldNavigator,
    MotorDriver,
    Navigator,
    TopDownMapper,
    Tunables,
    VisionProcessor,
    WorldView,
    build_arg_parser,
    load_tunables,
    save_tunables,
    write_json_report,
)


class DummyBuzzer:
    def __init__(self):
        self.events = []

    def pattern(self, name):
        self.events.append(name)


def make_frame(line_x=None, green=None, red=False):
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    if line_x is not None:
        cv2.line(frame, (line_x, 112), (line_x, 239), (0, 0, 0), 14)
    if green == "left":
        cv2.circle(frame, (95, 190), 14, (0, 180, 0), -1)
    elif green == "right":
        cv2.circle(frame, (225, 190), 14, (0, 180, 0), -1)
    elif green == "both":
        cv2.circle(frame, (95, 190), 14, (0, 180, 0), -1)
        cv2.circle(frame, (225, 190), 14, (0, 180, 0), -1)
    if red:
        cv2.circle(frame, (160, 198), 15, (0, 0, 220), -1)
    return frame


def make_parallel_frame():
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.line(frame, (78, 112), (78, 239), (0, 0, 0), 14)
    cv2.line(frame, (160, 112), (160, 239), (0, 0, 0), 14)
    return frame


def make_intersection_frame():
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.line(frame, (160, 105), (160, 239), (0, 0, 0), 14)
    cv2.line(frame, (62, 175), (258, 175), (0, 0, 0), 14)
    return frame


def make_world_frame(red_y=218):
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.line(frame, (160, 40), (160, 238), (0, 0, 0), 14)
    cv2.line(frame, (45, red_y), (275, red_y), (0, 0, 220), 12)
    return frame


def main():
    vision = VisionProcessor()
    motor = MotorDriver(dry_run=True)
    motor.buzzer = DummyBuzzer()

    result = vision.process(make_frame(160))
    print("center", result.line_seen, round(result.error, 3), result.sensor_states, result.special_state)
    assert result.line_seen
    assert abs(result.error) < 0.08

    human_vision = VisionProcessor()
    human_vision._human_frame_counter = 0
    human_vision._detect_humans = lambda frame: [(134, 96, 52, 150)]
    result = human_vision.process(make_frame(160))
    print("human-mask", result.line_seen, len(result.human_detections), result.human_masked_area_px)
    assert not result.line_seen
    assert len(result.human_detections) == 1
    assert result.human_masked_area_px > 0

    result = vision.process(make_parallel_frame())
    print("parallel", result.line_center_x, len(result.line_candidates), round(result.error, 3))
    assert result.line_seen
    assert len(result.line_candidates) >= 2
    assert abs(result.line_center_x - 160) <= 10

    result = vision.process(make_intersection_frame())
    print("intersection", result.intersection, result.intersection_branch_count, result.special_state)
    assert result.intersection
    assert result.intersection_branch_count >= 2

    mapper = TopDownMapper(output_size=(320, 240))
    mapper.src_ratios = np.array([[0, 1], [1, 1], [1, 0], [0, 0]], dtype=np.float32)
    mapper.dst_points = np.array([[0, 239], [319, 239], [319, 0], [0, 0]], dtype=np.float32)
    world = mapper.process(make_world_frame())
    print("world-map", world.line_seen, round(world.error, 3), world.red_line_seen, world.red_line_y)
    assert world.line_seen
    assert abs(world.error) < 0.08
    assert world.red_line_seen

    world_motor = MotorDriver(dry_run=True)
    world_motor.buzzer = DummyBuzzer()
    expert = ExpertWorldNavigator(Tunables(), world_motor)
    empty_mask = np.zeros((240, 320), dtype=np.uint8)
    start_view = WorldView(warped=make_world_frame(), black_mask=empty_mask, red_mask=empty_mask, red_line_seen=True)
    left, right, state, turn = expert.update(start_view)
    print("world-start", state, left, right)
    assert state == "START_RED_SEEN"
    clear_view = WorldView(warped=make_world_frame(), black_mask=empty_mask, red_mask=empty_mask, line_seen=True, error=0.0)
    left, right, state, turn = expert.update(clear_view)
    print("world-clear", state, left, right)
    assert state == "NAVIGATE_WORLD"
    expert.start_seen_time = time_start = expert.start_seen_time - 1.0 if expert.start_seen_time else None
    finish_view = WorldView(warped=make_world_frame(), black_mask=empty_mask, red_mask=empty_mask, red_line_seen=True)
    left, right, state, turn = expert.update(finish_view)
    print("world-finish", state, left, right, time_start is not None)
    assert state == "STOP_FINISH_RED"
    world_motor.close()

    result = vision.process(make_frame(160))
    nav = Navigator(Tunables(), motor)
    left, right, state, turn = nav.update(result, None)
    print("follow", round(left, 3), round(right, 3), state, round(turn, 3))
    assert state == "FOLLOW"
    assert left > 0 and right > 0

    result = vision.process(make_frame(215))
    left, right, state, turn = nav.update(result, None)
    print("right-error", round(result.error, 3), round(left, 3), round(right, 3), round(turn, 3))
    assert result.error > 0.20
    assert left > right

    result = vision.process(make_frame(None))
    left, right, state, turn = nav.update(result, 3.0)
    print("gap", result.line_seen, state, round(left, 3), round(right, 3))
    assert not result.line_seen
    assert state.startswith("GAP")

    nav = Navigator(Tunables(marker_mode="prelim", green_turns_enabled=False), motor)
    result = vision.process(make_frame(160, green="left"))
    left, right, state, turn = nav.update(result, None)
    print("green-prelim", result.green_left, state, motor.buzzer.events[-1])
    assert result.green_left
    assert state == "FOLLOW"
    assert motor.buzzer.events[-1] == "green"

    nav = Navigator(Tunables(marker_mode="final", green_turns_enabled=True), motor)
    result = vision.process(make_frame(160, green="left"))
    left, right, state, turn = nav.update(result, None)
    print("green-final", result.green_left, state)
    assert state.startswith("TURN_LEFT")

    nav = Navigator(Tunables(marker_mode="final", green_turns_enabled=True), motor)
    result = vision.process(make_frame(160, green="right"))
    left, right, state, turn = nav.update(result, None)
    print("green-right-final", result.green_right, state)
    assert result.green_right
    assert state.startswith("TURN_RIGHT")

    nav = Navigator(Tunables(marker_mode="final", green_turns_enabled=True), motor)
    result = vision.process(make_frame(160, green="both"))
    left, right, state, turn = nav.update(result, None)
    print("green-both-final", result.green_left, result.green_right, state)
    assert result.green_left and result.green_right
    assert state.startswith("TURN_U")

    nav = Navigator(Tunables(marker_mode="prelim", green_turns_enabled=False), motor)
    result = vision.process(make_frame(160, red=True))
    left, right, state, turn = nav.update(result, None)
    print("red", result.red_stop, state, left, right)
    assert result.red_stop
    assert state == "STOP_RED"
    assert left == 0 and right == 0

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "tunables.json"
        saved = Tunables(kp=1.23, ki=0.04, kd=0.56, base_speed=0.44, max_speed=0.77)
        loaded = Tunables()
        save_tunables(path, saved)
        assert load_tunables(path, loaded)
        print("tuning", loaded.kp, loaded.ki, loaded.kd, loaded.base_speed, loaded.max_speed)
        assert loaded.kp == saved.kp
        assert loaded.ki == saved.ki
        assert loaded.kd == saved.kd
        assert loaded.base_speed == saved.base_speed
        assert loaded.max_speed == saved.max_speed
        report = Path(temp_dir) / "report.json"
        write_json_report(report, {"kind": "smoke", "ok": True})
        assert report.exists()

    args = build_arg_parser().parse_args(["--self-test", "--dry-run", "--no-imu"])
    print("parser", args.self_test, args.dry_run, args.no_imu)
    assert args.self_test
    assert args.dry_run
    assert args.no_imu

    args = build_arg_parser().parse_args(["--benchmark", "--benchmark-frames", "25", "--benchmark-require-100hz"])
    print("benchmark-parser", args.benchmark, args.benchmark_frames, args.benchmark_require_100hz)
    assert args.benchmark
    assert args.benchmark_frames == 25
    assert args.benchmark_require_100hz

    args = build_arg_parser().parse_args(["--benchmark", "--report-file", "reports/benchmark.json"])
    print("report-parser", args.benchmark, args.report_file)
    assert args.benchmark
    assert args.report_file == "reports/benchmark.json"

    args = build_arg_parser().parse_args(["--motor-only-test", "--motor-test-duty", "0.75", "--motor-test-seconds", "1.0"])
    print("motor-parser", args.motor_only_test, args.motor_test_duty, args.motor_test_seconds)
    assert args.motor_only_test
    assert args.motor_test_duty == 0.75
    assert args.motor_test_seconds == 1.0

    args = build_arg_parser().parse_args(["--world-model", "--dry-run", "--world-size", "240", "--world-display"])
    print("world-parser", args.world_model, args.dry_run, args.world_size, args.world_display)
    assert args.world_model
    assert args.dry_run
    assert args.world_size == 240
    assert args.world_display

    motor.close()
    print("SMOKE PASS")


if __name__ == "__main__":
    main()
