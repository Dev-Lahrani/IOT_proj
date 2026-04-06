import RPi.GPIO as GPIO
import time
import threading


class HardwareAlerts:
    """Controls buzzer, vibration motor, and LED on Raspberry Pi GPIO."""

    def __init__(self, config):
        self.config = config
        self.buzzer_pin = config["buzzer_pin"]
        self.vibration_pin = config["vibration_pin"]
        self.led_pin = config["led_pin"]

        self.buzzer_enabled = config["buzzer_enabled"]
        self.vibration_enabled = config["vibration_enabled"]
        self.led_enabled = config["led_enabled"]

        self.buzzer_duration = config["buzzer_duration"]
        self.vibration_duration = config["vibration_duration"]
        self.led_blink_count = config["led_blink_count"]

        self._alert_lock = threading.Lock()
        self._running = False

        self._setup_gpio()

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if self.buzzer_enabled:
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

        if self.vibration_enabled:
            GPIO.setup(self.vibration_pin, GPIO.OUT)
            GPIO.output(self.vibration_pin, GPIO.LOW)

        if self.led_enabled:
            GPIO.setup(self.led_pin, GPIO.OUT)
            GPIO.output(self.led_pin, GPIO.LOW)

        self._running = True

    def trigger(self, alert_type="drowsy"):
        """Trigger all hardware alerts in a non-blocking thread."""
        if not self._running:
            return

        if not self._alert_lock.acquire(blocking=False):
            return

        t = threading.Thread(target=self._run_alerts, daemon=True)
        t.start()

    def _run_alerts(self, alert_type="drowsy"):
        try:
            threads = []

            if self.buzzer_enabled:
                t = threading.Thread(
                    target=self._buzzer_pulse,
                    args=(3 if alert_type == "drowsy" else 2,),
                    daemon=True,
                )
                t.start()
                threads.append(t)

            if self.vibration_enabled:
                t = threading.Thread(target=self._vibrate, daemon=True)
                t.start()
                threads.append(t)

            if self.led_enabled:
                t = threading.Thread(target=self._blink_led, daemon=True)
                t.start()
                threads.append(t)

            for t in threads:
                t.join()
        finally:
            self._alert_lock.release()

    def _buzzer_pulse(self, cycles=3):
        for _ in range(cycles):
            if not self._running:
                break
            GPIO.output(self.buzzer_pin, GPIO.HIGH)
            time.sleep(self.buzzer_duration)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            time.sleep(self.buzzer_duration)

    def _vibrate(self):
        GPIO.output(self.vibration_pin, GPIO.HIGH)
        time.sleep(self.vibration_duration)
        GPIO.output(self.vibration_pin, GPIO.LOW)

    def _blink_led(self):
        for _ in range(self.led_blink_count):
            if not self._running:
                break
            GPIO.output(self.led_pin, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(self.led_pin, GPIO.LOW)
            time.sleep(0.15)

    def cleanup(self):
        self._running = False
        if self.buzzer_enabled:
            GPIO.output(self.buzzer_pin, GPIO.LOW)
        if self.vibration_enabled:
            GPIO.output(self.vibration_pin, GPIO.LOW)
        if self.led_enabled:
            GPIO.output(self.led_pin, GPIO.LOW)
        GPIO.cleanup()
