import sys
import time
import unittest.mock as mock

sys.path.append("/Users/roopalisingh/Downloads/TemuFollower")

# We need to mock cv2 and serial before importing main
mock_cv2 = mock.MagicMock()
mock_cv2.waitKey.return_value = 0
mock_cv2.imshow = mock.MagicMock()

# Mock the serial port connection in hardware
mock_serial = mock.MagicMock()
sys.modules['cv2'] = mock_cv2
sys.modules['serial'] = mock_serial

# Now import modules
import main
from vision import VisionAgent
from feedback import FeedbackController

def run_main_loop_test():
    print("Starting simulated main loop timing test...")
    
    num_frames = 100
    
    # Create fake frames
    fake_frames = [object() for _ in range(num_frames)]
    
    # Mock process_frame to simulate green/red dots and stuck state
    def mock_process_frame(self, frame):
        idx = getattr(self, "_call_count", 0)
        self._call_count = idx + 1
        
        result = {
            "line_center_x": 160,
            "line_center_y": 120,
            "obstacle_detected": False,
            "obstacle_box": None,
            "special_state": None,
            "cnn_layers": None,
            "green_dot_detected": False,
            "red_dot_detected": False
        }
        
        # Stress-test: Switch state every 5 frames
        if idx % 20 < 5:
            result["green_dot_detected"] = True
        elif idx % 20 < 10:
            result["red_dot_detected"] = True
            result["special_state"] = "stop_line"
        
        return result

    # Patch the methods
    VisionAgent.process_frame = mock_process_frame
    VisionAgent._call_count = 0
    
    # We also mock StuckDetector to trigger stuck alarm when idx % 20 is between 10 and 15
    def mock_is_stuck(self, left_speed, right_speed):
        idx = VisionAgent._call_count
        if 10 <= (idx % 20) < 15:
            return True
        return False
    main.StuckDetector.is_stuck = mock_is_stuck

    # We want to measure the cycle times in main.py.
    # Let's patch get_frame to record timestamps and simulate 30 FPS timing.
    timestamps = []
    
    def timing_get_frame(self):
        for f in fake_frames:
            timestamps.append(time.time())
            # Sleep to simulate the time a 30 FPS camera takes to retrieve a frame (~33.3ms)
            time.sleep(1.0 / 30.0)
            yield f
            
    VisionAgent.get_frame = timing_get_frame

    # Execute main()
    # We save the original sleep to prevent infinite recursion
    original_sleep = time.sleep
    with mock.patch("time.sleep") as mock_sleep:
        def side_effect(secs):
            if secs == 1.0:
                print("[Mock] Skipping camera warm up sleep (1s)")
                return
            original_sleep(secs)
        mock_sleep.side_effect = side_effect
        
        start_test = time.time()
        main.main()
        end_test = time.time()
        
    print(f"\nSimulated main loop ran in {end_test - start_test:.2f} seconds.")
    
    # Calculate cycle intervals
    intervals = []
    for i in range(1, len(timestamps)):
        intervals.append(timestamps[i] - timestamps[i-1])
        
    if intervals:
        max_interval = max(intervals) * 1000
        avg_interval = sum(intervals) / len(intervals) * 1000
        fps = 1000.0 / avg_interval
        print("\n--- Main Loop Timing Summary ---")
        print(f"Max interval between loop cycles: {max_interval:.2f} ms")
        print(f"Avg interval between loop cycles: {avg_interval:.2f} ms")
        print(f"Effective loop frequency: {fps:.2f} FPS")
        
        # Check how many cycles exceeded 40ms (which degrades 30 FPS)
        slow_cycles = [i for i, v in enumerate(intervals) if v > 0.040]
        print(f"Cycles exceeding 40ms: {len(slow_cycles)} out of {len(intervals)}")
        for idx in slow_cycles[:10]:
            print(f"  Cycle {idx}: {intervals[idx]*1000:.2f} ms")

if __name__ == "__main__":
    run_main_loop_test()
