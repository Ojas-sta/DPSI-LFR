import sys
import time
import threading
import queue

sys.path.append("/Users/roopalisingh/Downloads/TemuFollower")

from feedback import FeedbackController

# Let's define the Mock LED/Buzzer locally for the queue controller
class LED:
    def __init__(self, pin): self.pin = pin
    def on(self): pass
    def off(self): pass

class QueueFeedbackController:
    def __init__(self, red_pin=5, green_pin=6, buzzer_pin=13):
        self.red_led = LED(red_pin)
        self.green_led = LED(green_pin)
        self.has_buzzer = False
        
        self.queue = queue.Queue()
        self.current_state = None
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._stop_worker = threading.Event()
        self.worker_thread.start()
        
        self.animation_thread = None
        self.animation_stop_event = threading.Event()

    def _worker_loop(self):
        while not self._stop_worker.is_set():
            try:
                state = self.queue.get(timeout=0.05)
                self._handle_state_change(state)
                self.queue.task_done()
            except queue.Empty:
                continue

    def _handle_state_change(self, state):
        if state == self.current_state:
            return
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_stop_event.set()
            self.animation_thread.join()
            
        self.current_state = state
        self.animation_stop_event.clear()
        
        if state == "green_dot":
            self.animation_thread = threading.Thread(
                target=self._blink_led_and_beep,
                args=(self.green_led, 523, 2.0, 0.2, 0.2)
            )
            self.animation_thread.start()
        elif state == "red_dot":
            self.animation_thread = threading.Thread(
                target=self._blink_led_and_beep,
                args=(self.red_led, 262, 10.0, 0.5, 0.5)
            )
            self.animation_thread.start()
        elif state == "stuck_alarm":
            self.animation_thread = threading.Thread(
                target=self._blink_led_and_beep,
                args=(self.red_led, 880, 5.0, 0.1, 0.1)
            )
            self.animation_thread.start()
        elif state == "armed":
            self.red_led.off()
            self.green_led.on()
        elif state == "disarmed":
            self.green_led.off()
            self.red_led.on()
        elif state == "cleanup":
            self.red_led.off()
            self.green_led.off()

    def _sleep(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            if self.animation_stop_event.is_set():
                break
            time.sleep(0.01)

    def _blink_led_and_beep(self, led, buzzer_tone=None, duration=2.0, blink_on=0.2, blink_off=0.2):
        end_time = time.time() + duration
        while time.time() < end_time and not self.animation_stop_event.is_set():
            led.on()
            self._sleep(blink_on)
            led.off()
            self._sleep(blink_off)
        led.off()

    def action_green_dot(self):
        self.queue.put("green_dot")

    def action_red_dot(self):
        self.queue.put("red_dot")

    def indicate_stuck_alarm(self):
        self.queue.put("stuck_alarm")

    def cleanup(self):
        self._stop_worker.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join()
        self._handle_state_change("cleanup")

def run_stress_test(controller, num_iterations=100):
    stats = []
    target_dt = 1.0 / 30.0  # 33.3ms
    
    for i in range(num_iterations):
        start_time = time.time()
        
        # Rapid state changes (alternating states every frame)
        if i % 3 == 0:
            controller.action_green_dot()
        elif i % 3 == 1:
            controller.action_red_dot()
        else:
            controller.indicate_stuck_alarm()
            
        end_time = time.time()
        duration = end_time - start_time
        
        elapsed = time.time() - start_time
        sleep_time = target_dt - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        stats.append({
            "api_call_duration": duration,
        })
        
    return stats

def main():
    print("Testing Original FeedbackController under rapid state changes...")
    orig_controller = FeedbackController()
    orig_stats = run_stress_test(orig_controller)
    orig_controller.cleanup()
    
    print("\nTesting Queue-based FeedbackController under rapid state changes...")
    queue_controller = QueueFeedbackController()
    queue_stats = run_stress_test(queue_controller)
    queue_controller.cleanup()
    
    orig_max = max(s["api_call_duration"] for s in orig_stats) * 1000
    orig_avg = sum(s["api_call_duration"] for s in orig_stats) / len(orig_stats) * 1000
    
    queue_max = max(s["api_call_duration"] for s in queue_stats) * 1000
    queue_avg = sum(s["api_call_duration"] for s in queue_stats) / len(queue_stats) * 1000
    
    print("\n================ COMPARISON RESULTS ================")
    print(f"Original FeedbackController:")
    print(f"  Max API call duration: {orig_max:.4f} ms")
    print(f"  Avg API call duration: {orig_avg:.4f} ms")
    print(f"\nQueue-based FeedbackController:")
    print(f"  Max API call duration: {queue_max:.4f} ms")
    print(f"  Avg API call duration: {queue_avg:.4f} ms")
    print(f"\nImprovement Factor (Avg): {orig_avg / max(1e-9, queue_avg):.1f}x faster API calls!")

if __name__ == "__main__":
    main()
