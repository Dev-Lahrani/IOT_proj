import cv2
import yaml
import time
import signal
import sys
import os
import requests
import numpy as np
from urllib.parse import urlparse
from hardware import HardwareAlerts
from gps import GPSReader
from publisher import DataPublisher


class MjpegStreamCamera:
    def __init__(self, url, timeout=10):
        self.url = url
        self.timeout = timeout
        self.stream = None
        self.buffer = b""
        self._connect()

    def _connect(self):
        try:
            self.stream = requests.get(self.url, stream=True, timeout=self.timeout)
            self.stream.raise_for_status()
            self.buffer = b""
            print(f"[Camera] Connected to {self.url}")
        except requests.RequestException as e:
            print(f"[Camera] Failed: {e}")
            self.stream = None

    def isOpened(self):
        return self.stream is not None

    def read(self):
        if self.stream is None:
            return False, None
        try:
            for chunk in self.stream.iter_content(chunk_size=4096):
                if not chunk:
                    continue
                self.buffer += chunk
                while True:
                    start = self.buffer.find(b"\xff\xd8")
                    end = self.buffer.find(b"\xff\xd9")
                    if start != -1 and end != -1:
                        jpg = self.buffer[start : end + 2]
                        self.buffer = self.buffer[end + 2 :]
                        frame = cv2.imdecode(
                            np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR
                        )
                        if frame is not None:
                            return True, frame
                    elif start == -1 and len(self.buffer) > 10000:
                        self.buffer = b""
                    else:
                        break
            return False, None
        except requests.RequestException as e:
            print(f"[Camera] Stream error: {e}, reconnecting...")
            self._connect()
            return False, None

    def release(self):
        if self.stream:
            self.stream.close()
            self.stream = None


def get_camera_url(config):
    def normalize_stream_url(url, default_path):
        if not isinstance(url, str):
            return url
        cleaned = url.strip()
        if not cleaned:
            return cleaned

        if "://" not in cleaned:
            cleaned = f"http://{cleaned.lstrip('/')}"

        parsed = urlparse(cleaned)
        if parsed.scheme in {"http", "https"} and parsed.path in {"", "/"}:
            return cleaned.rstrip("/") + default_path
        return cleaned

    source = config["camera"]["source"]
    if source == "phone":
        return normalize_stream_url(config["camera"]["phone_url"], "/video")
    if source == "esp32":
        return normalize_stream_url(config["camera"]["esp32_url"], "/stream")
    if source == "usb":
        return config["camera"]["usb_device"]
    if source == "picam":
        return config["camera"]["picam_index"]
    return normalize_stream_url(config["camera"]["esp32_url"], "/stream")


def open_camera(source, timeout=10):
    if isinstance(source, str) and (
        source.startswith("http://") or source.startswith("https://")
    ):
        cap = MjpegStreamCamera(source, timeout)
        if cap.isOpened():
            return cap
        return None
    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    start = time.time()
    while time.time() - start < timeout:
        ret, _ = cap.read()
        if ret:
            return cap
        time.sleep(0.5)
    return None


def load_cascades():
    base = cv2.data.haarcascades
    face = cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml")
    eye = cv2.CascadeClassifier(base + "haarcascade_eye.xml")
    if face.empty() or eye.empty():
        raise RuntimeError("Failed to load Haar cascades")
    return face, eye


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    det = config["detection"]
    hw_config = config["hardware"]
    gps_config = config["gps"]
    dash_config = config["dashboard"]
    cooldown_config = config["alert_cooldown"]
    show_preview = bool(os.environ.get("DISPLAY"))
    hardware = HardwareAlerts(hw_config)
    gps = GPSReader(gps_config)
    publisher = DataPublisher(dash_config)
    publisher.start()
    face_cascade, eye_cascade = load_cascades()
    eye_closed_counter = 0
    status = "ALERT"
    last_drowsy_alert = 0
    frame_count = 0
    closed_frames_threshold = max(5, det["ear_consecutive_frames"] // 2)
    camera_source = get_camera_url(config)
    cap = open_camera(camera_source)
    if cap is None:
        print("[Camera] No camera source. Exiting.")
        hardware.cleanup()
        gps.stop()
        publisher.stop()
        sys.exit(1)
    print("[System] Monitoring driver...")

    def shutdown(sig, frame):
        print("\n[System] Shutting down...")
        hardware.cleanup()
        gps.stop()
        publisher.stop()
        cap.release()
        if show_preview:
            cv2.destroyAllWindows()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        frame_count += 1
        if frame_count % det["frame_skip"] != 0:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )
        status = "ALERT"
        current_ear = 0.0
        current_mar = 0.0
        eyes_detected = 0
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            face_roi_gray = gray[y : y + h, x : x + w]
            eyes = eye_cascade.detectMultiScale(
                face_roi_gray, scaleFactor=1.1, minNeighbors=6, minSize=(20, 20)
            )
            eyes_detected = len(eyes)
            for ex, ey, ew, eh in eyes[:2]:
                cv2.rectangle(
                    frame, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (0, 255, 0), 2
                )
            if eyes_detected == 0:
                eye_closed_counter += 1
            else:
                eye_closed_counter = 0
            if eye_closed_counter >= closed_frames_threshold:
                now = time.time()
                if now - last_drowsy_alert > cooldown_config["drowsy_cooldown"]:
                    hardware.trigger("drowsy")
                    last_drowsy_alert = now
                status = "DROWSY"
        else:
            eye_closed_counter = 0
        color = (0, 255, 0) if status == "ALERT" else (0, 0, 255)
        cv2.putText(
            frame,
            f"Status: {status}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            frame,
            f"Eyes: {eyes_detected}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        lat, lon = gps.get_coordinates()
        publisher.push(
            {
                "ear": round(current_ear, 3),
                "mar": round(current_mar, 3),
                "status": status,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )
        if show_preview:
            cv2.imshow("Driver Monitoring", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    hardware.cleanup()
    gps.stop()
    publisher.stop()
    cap.release()
    if show_preview:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
