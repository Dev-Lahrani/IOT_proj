import serial
import pynmea2
import time
import threading


class GPSReader:
    """Reads GPS coordinates from Neo-6M module via serial."""

    def __init__(self, config):
        self.port = config["port"]
        self.baudrate = config["baudrate"]
        self.fallback_lat = config["fallback_lat"]
        self.fallback_lon = config["fallback_lon"]

        self._lat = self.fallback_lat
        self._lon = self.fallback_lon
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._serial = None

        self._connect()

    def _connect(self):
        try:
            self._serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1,
            )
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            return True
        except (serial.SerialException, OSError):
            print(f"[GPS] Could not open {self.port}, using fallback coordinates")
            self._running = False
            return False

    def _read_loop(self):
        while self._running:
            try:
                line = self._serial.readline().decode("ascii", errors="ignore").strip()
                if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                    msg = pynmea2.parse(line)
                    if msg.latitude and msg.longitude:
                        with self._lock:
                            self._lat = msg.latitude
                            self._lon = msg.longitude
            except (pynmea2.ParseError, ValueError):
                continue
            except serial.SerialException:
                time.sleep(1)

    def get_coordinates(self):
        with self._lock:
            return self._lat, self._lon

    def stop(self):
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()
