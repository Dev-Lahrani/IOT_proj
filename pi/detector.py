import cv2
import yaml
import time
import signal
import sys
import os

from hardware import HardwareAlerts
from gps import GPSReader
from publisher import DataPublisher


def get_camera_url(config):
    source = config["camera"]["source"]
    if source == "phone":
        return config["camera"]["phone_url"]
    if source == "esp32":
        return config["camera"]["esp32_url"]
    if source == "usb":
        return config["camera"]["usb_device"]
    if source == "picam":
        return config["camera"]["picam_index"]
    return config["camera"]["esp32_url"]


def open_camera(source, timeout=10):
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
        raise RuntimeError("Failed to load OpenCV Haar cascades")

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

    if cap is None and config["camera"].get("fallback_enabled") and isinstance(
        camera_source, str
    ):
        print("[Camera] Primary source failed, trying fallback...")
        alt = (
            config["camera"]["esp32_url"]
            if camera_source == config["camera"]["phone_url"]
            else config["camera"]["phone_url"]
        )
        cap = open_camera(alt)

    if cap is None:
        print("[Camera] No camera source available. Exiting.")
        hardware.cleanup()
        gps.stop()
        publisher.stop()
        sys.exit(1)

    print("[System] OpenCV detector initialized. Monitoring driver...")

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
            continue

        frame_count += 1
        if frame_count % det["frame_skip"] != 0:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80),
        )

        status = "ALERT"
        current_ear = 0.0
        current_mar = 0.0
        eyes_detected = 0

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            face_roi_gray = gray[y : y + h, x : x + w]
            face_roi_color = frame[y : y + h, x : x + w]

            eyes = eye_cascade.detectMultiScale(
                face_roi_gray,
                scaleFactor=1.1,
                minNeighbors=6,
                minSize=(20, 20),
            )

            eyes_detected = len(eyes)

            for ex, ey, ew, eh in eyes[:2]:
                cv2.rectangle(
                    face_roi_color,
                    (ex, ey),
                    (ex + ew, ey + eh),
                    (0, 255, 0),
                    2,
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

        color_map = {
            "ALERT": (0, 255, 0),
            "DROWSY": (0, 0, 255),
        }
        color = color_map.get(status, (255, 255, 255))

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
            f"Eyes Detected: {eyes_detected}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Closed Count: {eye_closed_counter}",
            (10, 90),
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
