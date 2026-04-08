import cv2
import dlib
import numpy as np
import yaml
import time
import signal
import sys
import os
from scipy.spatial import distance as dist
from hardware import HardwareAlerts
from gps import GPSReader
from publisher import DataPublisher


FACIAL_LANDMARKS_68_IDXS = {
    "mouth": (48, 68),
    "inner_mouth": (60, 68),
    "right_eyebrow": (17, 22),
    "left_eyebrow": (22, 27),
    "right_eye": (36, 42),
    "left_eye": (42, 48),
    "nose": (27, 35),
    "jaw": (0, 17),
}


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])
    C = dist.euclidean(mouth[0], mouth[6])
    return (A + B) / (2.0 * C)


def shape_to_np(shape, dtype="int"):
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def get_camera_url(config):
    source = config["camera"]["source"]
    if source == "phone":
        return config["camera"]["phone_url"]
    elif source == "esp32":
        return config["camera"]["esp32_url"]
    elif source == "usb":
        return config["camera"]["usb_device"]
    elif source == "picam":
        return config["camera"]["picam_index"]
    return config["camera"]["phone_url"]


def open_camera(source, timeout=10):
    if isinstance(source, str):
        cap = cv2.VideoCapture(source)
    else:
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

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    (l_start, l_end) = FACIAL_LANDMARKS_68_IDXS["left_eye"]
    (r_start, r_end) = FACIAL_LANDMARKS_68_IDXS["right_eye"]
    (m_start, m_end) = FACIAL_LANDMARKS_68_IDXS["mouth"]

    ear_counter = 0
    mar_counter = 0
    status = "ALERT"
    last_drowsy_alert = 0
    last_yawn_alert = 0
    frame_count = 0

    camera_source = get_camera_url(config)
    cap = open_camera(camera_source)

    if cap is None:
        if config["camera"].get("fallback_enabled") and isinstance(camera_source, str):
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

    print("[System] All modules initialized. Monitoring driver...")

    def shutdown(sig, frame):
        print("\n[System] Shutting down...")
        hardware.cleanup()
        gps.stop()
        publisher.stop()
        cap.release()
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
        faces = detector(gray, 0)

        current_ear = 0.0
        current_mar = 0.0
        status = "ALERT"

        for face in faces:
            shape = predictor(gray, face)
            shape = shape_to_np(shape)

            left_eye = shape[l_start:l_end]
            right_eye = shape[r_start:r_end]
            mouth = shape[m_start:m_end]

            current_ear = (
                eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)
            ) / 2.0
            current_mar = mouth_aspect_ratio(mouth)

            if current_ear < det["ear_threshold"]:
                ear_counter += 1
                if ear_counter > det["ear_consecutive_frames"]:
                    now = time.time()
                    if now - last_drowsy_alert > cooldown_config["drowsy_cooldown"]:
                        status = "DROWSY"
                        hardware.trigger("drowsy")
                        last_drowsy_alert = now
            else:
                ear_counter = 0

            if current_mar > det["mar_threshold"]:
                mar_counter += 1
                if mar_counter > det["mar_consecutive_frames"]:
                    now = time.time()
                    if now - last_yawn_alert > cooldown_config["yawn_cooldown"]:
                        status = "YAWNING"
                        hardware.trigger("yawn")
                        last_yawn_alert = now
            else:
                mar_counter = 0

            for start, end in [
                (l_start, l_end),
                (r_start, r_end),
                (m_start, m_end),
            ]:
                pts = shape[start:end]
                cv2.polylines(frame, [pts], True, (0, 255, 0), 1)

            (x, y, w, h) = cv2.boundingRect(
                np.array(
                    [
                        shape[l_start:l_end][0],
                        shape[r_start:r_end][-1],
                        shape[m_start:m_end][2],
                    ]
                )
            )
            cv2.rectangle(
                frame,
                (face.left(), face.top()),
                (face.right(), face.bottom()),
                (255, 0, 0),
                2,
            )

        color_map = {
            "ALERT": (0, 255, 0),
            "DROWSY": (0, 0, 255),
            "YAWNING": (0, 165, 255),
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
            f"EAR: {current_ear:.3f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"MAR: {current_mar:.3f}",
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
