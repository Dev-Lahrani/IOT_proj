#!/usr/bin/env python3
"""
Host-side drowsiness detector.

Pulls MJPEG frames from the ESP32-CAM module URL, runs MediaPipe Face Mesh
to compute EAR (Eye Aspect Ratio) and MAR (Mouth Aspect Ratio), then:
  - Publishes detection status to vehicle/driver/status  (→ dashboard)
  - Publishes alert commands  to vehicle/alerts           (→ ESP32 controller)

GPS coordinates are received from the ESP32 controller via vehicle/gps and
merged into each status publish.

Run alongside dashboard/backend/app.py:
    python dashboard_backend/detector.py
"""

import json
import os
import sys
import time
import threading
from datetime import datetime

import cv2
import mediapipe as mp
import numpy as np
import paho.mqtt.client as mqtt
import yaml

# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices
# ---------------------------------------------------------------------------
# Eye points: [p1=corner, p2=upper-outer, p3=upper-inner,
#              p4=corner, p5=lower-inner, p6=lower-outer]
LEFT_EYE  = [33,  160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Mouth points used for MAR
MOUTH_TOP    = 13   # upper inner lip
MOUTH_BOTTOM = 14   # lower inner lip
MOUTH_LEFT   = 61   # left corner
MOUTH_RIGHT  = 291  # right corner


def _dist(a, b):
    return float(np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float)))


def _pt(lm, idx, w, h):
    return (lm[idx].x * w, lm[idx].y * h)


def eye_aspect_ratio(landmarks, indices, w, h):
    p = [_pt(landmarks, i, w, h) for i in indices]
    vertical = _dist(p[1], p[5]) + _dist(p[2], p[4])
    horizontal = _dist(p[0], p[3])
    return vertical / (2.0 * horizontal + 1e-6)


def mouth_aspect_ratio(landmarks, w, h):
    top    = _pt(landmarks, MOUTH_TOP,    w, h)
    bottom = _pt(landmarks, MOUTH_BOTTOM, w, h)
    left   = _pt(landmarks, MOUTH_LEFT,   w, h)
    right  = _pt(landmarks, MOUTH_RIGHT,  w, h)
    return _dist(top, bottom) / (_dist(left, right) + 1e-6)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------
class DrowsinessDetector:
    def __init__(self, config: dict):
        cam    = config["camera"]
        det    = config["detection"]
        dash   = config["dashboard"]
        cool   = config.get("alert_cooldown", {})

        self.cam_url      = cam["esp32_url"]
        self.ear_thresh   = det["ear_threshold"]
        self.mar_thresh   = det["mar_threshold"]
        self.ear_frames   = det["ear_consecutive_frames"]
        self.mar_frames   = det["mar_consecutive_frames"]
        self.frame_skip   = det.get("frame_skip", 2)
        self.drowsy_cool  = cool.get("drowsy_cooldown", 10)
        self.yawn_cool    = cool.get("yawn_cooldown", 15)

        self._eye_ctr     = 0
        self._mouth_ctr   = 0
        self._last_drowsy = 0.0
        self._last_yawn   = 0.0
        self._frame_n     = 0

        # Shared GPS state — updated by MQTT subscription in a background thread
        self._gps_lock = threading.Lock()
        self._lat      = 0.0
        self._lon      = 0.0

        # MediaPipe
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # MQTT
        broker            = dash.get("mqtt_broker", "localhost")
        port              = int(dash.get("mqtt_port", 1883))
        self._status_topic = dash.get("mqtt_topic", "vehicle/driver/status")
        self._alert_topic  = "vehicle/alerts"
        self._gps_topic    = "vehicle/gps"

        self._mq = mqtt.Client()
        self._mq.on_message = self._on_mqtt_message
        try:
            self._mq.connect(broker, port, keepalive=60)
            self._mq.subscribe(self._gps_topic)
            self._mq.loop_start()
            print(f"[Detector] MQTT connected to {broker}:{port}")
        except Exception as exc:
            print(f"[Detector] MQTT unavailable: {exc}")

    def _on_mqtt_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            with self._gps_lock:
                self._lat = float(data.get("latitude", self._lat))
                self._lon = float(data.get("longitude", self._lon))
        except Exception:
            pass

    def _publish(self, status: str, ear: float, mar: float, alert: bool):
        with self._gps_lock:
            lat, lon = self._lat, self._lon

        payload = json.dumps({
            "status":          status,
            "ear":             round(ear, 3),
            "mar":             round(mar, 3),
            "latitude":        lat,
            "longitude":       lon,
            "timestamp":       datetime.now().isoformat(),
            "alert_triggered": alert,
        })
        self._mq.publish(self._status_topic, payload)

        if alert:
            cmd = json.dumps({"type": status.lower()})
            self._mq.publish(self._alert_topic, cmd)

    def run(self):
        print(f"[Detector] Opening stream: {self.cam_url}")
        cap = cv2.VideoCapture(self.cam_url)
        if not cap.isOpened():
            print("[Detector] Cannot open camera stream — check cam_url in config.yaml")
            return

        status = "NO_FACE"
        ear = mar = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[Detector] Stream lost, reconnecting in 3 s...")
                    cap.release()
                    time.sleep(3)
                    cap = cv2.VideoCapture(self.cam_url)
                    continue

                self._frame_n += 1
                if self._frame_n % self.frame_skip != 0:
                    continue

                h, w = frame.shape[:2]
                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res  = self._mesh.process(rgb)

                alert = False

                if not res.multi_face_landmarks:
                    status = "NO_FACE"
                    self._eye_ctr = self._mouth_ctr = 0
                    ear = mar = 0.0
                else:
                    lm  = res.multi_face_landmarks[0].landmark
                    ear = (eye_aspect_ratio(lm, LEFT_EYE,  w, h) +
                           eye_aspect_ratio(lm, RIGHT_EYE, w, h)) / 2.0
                    mar = mouth_aspect_ratio(lm, w, h)
                    now = time.time()

                    # Drowsiness check
                    if ear < self.ear_thresh:
                        self._eye_ctr += 1
                        if self._eye_ctr >= self.ear_frames:
                            if now - self._last_drowsy >= self.drowsy_cool:
                                status = "DROWSY"
                                alert  = True
                                self._last_drowsy = now
                                print(f"[Detector] DROWSY  EAR={ear:.3f}")
                    else:
                        self._eye_ctr = max(0, self._eye_ctr - 1)

                    # Yawn check
                    if mar > self.mar_thresh:
                        self._mouth_ctr += 1
                        if self._mouth_ctr >= self.mar_frames:
                            if now - self._last_yawn >= self.yawn_cool:
                                status = "YAWN"
                                alert  = True
                                self._last_yawn = now
                                print(f"[Detector] YAWN    MAR={mar:.3f}")
                    else:
                        self._mouth_ctr = max(0, self._mouth_ctr - 1)

                    if not alert and status in ("DROWSY", "YAWN", "NO_FACE"):
                        status = "NORMAL"

                self._publish(status, ear, mar, alert)

        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            self._mesh.close()
            self._mq.loop_stop()
            print("[Detector] Stopped")


def main():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "legacy_pi", "config.yaml")
    with open(cfg_path) as f:
        config = yaml.safe_load(f)
    DrowsinessDetector(config).run()


if __name__ == "__main__":
    main()
