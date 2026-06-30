import time
import threading

try:
    from gpiozero import LED, TonalBuzzer
except ImportError:
    print("Warning: gpiozero not found. Running feedback in mock mode.")
    class LED:
        def __init__(self, pin): self.pin = pin
        def on(self): pass
        def off(self): pass
    class TonalBuzzer:
        def __init__(self, pin): self.pin = pin
        def play(self, tone): pass
        def stop(self): pass


class FeedbackController:
    def __init__(self, red_pin=5, green_pin=6, buzzer_pin=13):
        """
        Initialize the feedback components.
        Maps the LEDs exactly as requested by the competition rules:
        - 1 Red LED
        - 1 Green LED
        - 1 Buzzer
        """
        self.red_led = LED(red_pin)
        self.green_led = LED(green_pin)
        
        try:
            self.buzzer = TonalBuzzer(buzzer_pin)
            self.has_buzzer = True
        except Exception:
            self.has_buzzer = False
            
        self.led_thread = None
        self._stop_event = threading.Event()

    def _blink_led_and_beep(self, led, buzzer_tone=None, duration=2.0, blink_on=0.2, blink_off=0.2):
        """Internal method to blink an LED and beep the buzzer in sync in a non-blocking thread."""
        end_time = time.time() + duration
        while time.time() < end_time and not self._stop_event.is_set():
            led.on()
            if buzzer_tone and self.has_buzzer:
                try:
                    self.buzzer.play(buzzer_tone)
                except Exception:
                    pass
            time.sleep(blink_on)
            led.off()
            if buzzer_tone and self.has_buzzer:
                try:
                    self.buzzer.stop()
                except Exception:
                    pass
            time.sleep(blink_off)
        led.off()
        if self.has_buzzer:
            try:
                self.buzzer.stop()
            except Exception:
                pass

    def action_green_dot(self):
        """
        Competition Rule: Green Dot -> Blink GREEN LED and continue movement.
        Plays a C5 (523Hz) tone. Runs in background.
        """
        print("[Feedback] Green Marker Detected -> Blinking GREEN LED & Beeping")
        
        # Stop any currently running animations
        if self.led_thread and self.led_thread.is_alive():
            self._stop_event.set()
            self.led_thread.join()
        
        self._stop_event.clear()
        self.led_thread = threading.Thread(
            target=self._blink_led_and_beep, 
            args=(self.green_led, 523, 2.0, 0.2, 0.2)
        )
        self.led_thread.start()

    def action_red_dot(self):
        """
        Competition Rule: Red Dot -> Stop completely and blink RED LED.
        Plays a lower pitch alarm tone C4 (262Hz) to signal stopping.
        """
        print("[Feedback] Red Marker Detected -> Blinking RED LED & Alarm Beeping (Stopping)")
        
        if self.led_thread and self.led_thread.is_alive():
            self._stop_event.set()
            self.led_thread.join()
            
        self._stop_event.clear()
        self.led_thread = threading.Thread(
            target=self._blink_led_and_beep, 
            args=(self.red_led, 262, 10.0, 0.5, 0.5)
        )
        self.led_thread.start()

    def indicate_armed(self):
        """Turns the green LED on solid to indicate the robot is armed and ready."""
        self._stop_event.set()
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join()
        self.red_led.off()
        self.green_led.on()
        if self.has_buzzer:
            try:
                self.buzzer.stop()
            except Exception:
                pass
        
    def indicate_disarmed(self):
        """Turns the red LED on solid to indicate the robot is safe/disarmed."""
        self._stop_event.set()
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join()
        self.green_led.off()
        self.red_led.on()
        if self.has_buzzer:
            try:
                self.buzzer.stop()
            except Exception:
                pass

    def indicate_stuck_alarm(self):
        """Flashes red rapidly and triggers high pitch alarm (A5: 880Hz) if IMU detects robot is stuck."""
        if self.led_thread and self.led_thread.is_alive():
            self._stop_event.set()
            self.led_thread.join()
            
        self._stop_event.clear()
        self.led_thread = threading.Thread(
            target=self._blink_led_and_beep, 
            args=(self.red_led, 880, 5.0, 0.1, 0.1)
        )
        self.led_thread.start()

    def cleanup(self):
        """Turn off all LEDs safely on shutdown."""
        self._stop_event.set()
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join()
        self.red_led.off()
        self.green_led.off()
        if self.has_buzzer:
            try:
                self.buzzer.stop()
            except Exception:
                pass
