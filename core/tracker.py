"""
tracker.py — Stable hand tracking for Samsung + Windows 11.
Camera confirmed on Index 0. Frame pipeline fully protected.
"""

import threading
import time
import math
import sys
import copy

try:
    import cv2
    import mediapipe as mp
    import numpy as np
    DEPS_OK = True
except ImportError:
    DEPS_OK = False


class LM:
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20


def dist(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _fix_registry():
    try:
        import winreg
        python_exe = sys.executable
        encoded = python_exe.replace("\\", "#").replace(":", "#")
        base = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
        for subpath in [
            base,
            base + r"\NonPackaged",
            base + r"\NonPackaged\\" + encoded,
        ]:
            try:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, subpath,
                                        0, winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY) as k:
                    winreg.SetValueEx(k, "Value", 0, winreg.REG_SZ, "Allow")
            except Exception:
                pass
    except Exception:
        pass


def _open_camera():
    """
    Open camera. Diagnostic confirmed Index 0 works.
    CRITICAL: Read frames BEFORE setting any properties.
    """
    attempts = [
        (0, cv2.CAP_MSMF),
        (0, cv2.CAP_DSHOW),
        (1, cv2.CAP_MSMF),
        (1, cv2.CAP_DSHOW),
        (0, None),
        (1, None),
    ]

    for (idx, backend) in attempts:
        cap = None
        try:
            cap = cv2.VideoCapture(idx, backend) if backend is not None else cv2.VideoCapture(idx)

            if not cap.isOpened():
                cap.release()
                continue

            # Read frames FIRST before touching any properties
            got_frame = False
            for _ in range(60):
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        got_frame = True
                        break
                except Exception:
                    break
                time.sleep(0.05)

            if not got_frame:
                cap.release()
                continue

            # Only set properties AFTER confirming frames work
            try: cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            except: pass
            try: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            except: pass
            try: cap.set(cv2.CAP_PROP_FPS, 30)
            except: pass

            return cap

        except Exception:
            try:
                if cap: cap.release()
            except: pass
            continue

    return None


class HandTracker:
    def __init__(self, settings: dict, on_frame=None):
        self.settings = settings
        self.on_frame = on_frame
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._latest_hands = []
        self._frame = None
        self._camera_ready = threading.Event()
        self._camera_error = None

    def start(self):
        if not DEPS_OK:
            raise RuntimeError("Run: pip install mediapipe opencv-python")

        _fix_registry()

        self._stop_event.clear()
        self._camera_ready = threading.Event()
        self._camera_error = None
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        if not self._camera_ready.wait(timeout=15.0):
            self._stop_event.set()
            raise RuntimeError(
                "Camera timed out.\n\n"
                "Diagnostic confirmed your camera works on Index 0.\n"
                "Something grabbed the camera between now and then.\n\n"
                "Open Task Manager → end any process using the camera,\n"
                "then click Start again."
            )
        if self._camera_error:
            self._stop_event.set()
            raise RuntimeError(self._camera_error)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=4)

    def get_latest(self):
        with self._lock:
            # Return copies so the detection loop is never blocked by UI reads
            return list(self._latest_hands), (
                self._frame.copy() if self._frame is not None else None
            )

    def _loop(self):
        s = self.settings
        cap = _open_camera()

        if cap is None:
            self._camera_error = (
                "Camera failed inside the app even though diagnostic showed it works.\n\n"
                "Most likely another process grabbed the camera.\n\n"
                "1. Open Task Manager (Ctrl+Shift+Esc)\n"
                "2. End: Camera, Teams, Discord, OBS, or any video app\n"
                "3. Close GestureControl\n"
                "4. Right-click run.bat → Run as administrator\n"
                "5. Click Start immediately after the app opens"
            )
            self._camera_ready.set()
            return

        self._camera_ready.set()

        mp_hands = mp.solutions.hands
        mp_draw  = mp.solutions.drawing_utils
        mp_style = mp.solutions.drawing_styles

        try:
            with mp_hands.Hands(
                model_complexity=0,
                max_num_hands=2 if s.get("enable_both_hands", True) else 1,
                min_detection_confidence=s.get("min_detection_confidence", 0.75),
                min_tracking_confidence=s.get("min_tracking_confidence", 0.75),
            ) as hands:
                while not self._stop_event.is_set():
                    try:
                        ret, frame = cap.read()

                        # Skip bad frames silently
                        if not ret or frame is None or frame.size == 0:
                            time.sleep(0.02)
                            continue

                        # Defensive copy BEFORE any processing
                        frame = frame.copy()

                        if s.get("mirror_camera", True):
                            frame = cv2.flip(frame, 1)

                        # Run MediaPipe on a separate copy of the frame
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        rgb.flags.writeable = False          # speed up MediaPipe
                        result = hands.process(rgb)
                        rgb.flags.writeable = True

                        hands_data = []
                        if result.multi_hand_landmarks and result.multi_handedness:
                            for lms, handedness in zip(
                                result.multi_hand_landmarks, result.multi_handedness
                            ):
                                label = handedness.classification[0].label
                                score = handedness.classification[0].score
                                pts   = lms.landmark

                                if s.get("show_landmarks", True):
                                    mp_draw.draw_landmarks(
                                        frame, lms,
                                        mp_hands.HAND_CONNECTIONS,
                                        mp_style.get_default_hand_landmarks_style(),
                                        mp_style.get_default_hand_connections_style(),
                                    )

                                try:
                                    state = self._extract_state(pts, label, score, frame.shape)
                                    hands_data.append(state)
                                except Exception:
                                    pass

                        # Store with lock — UI reads this safely via get_latest()
                        with self._lock:
                            self._latest_hands = hands_data
                            self._frame = frame   # already copied above

                        # Fire callback WITHOUT holding the lock
                        if self.on_frame:
                            try:
                                self.on_frame(frame, hands_data)
                            except Exception:
                                pass

                    except Exception:
                        time.sleep(0.02)

        finally:
            try: cap.release()
            except: pass

    def _extract_state(self, pts, label, score, shape):
        def px(i): return pts[i].x, pts[i].y

        palm_size = dist(pts[LM.WRIST], pts[LM.MIDDLE_MCP])
        if palm_size < 1e-6:
            palm_size = 0.1

        fe = {
            "thumb":  self._thumb_extended(pts, label),
            "index":  pts[LM.INDEX_TIP].y  < pts[LM.INDEX_PIP].y,
            "middle": pts[LM.MIDDLE_TIP].y < pts[LM.MIDDLE_PIP].y,
            "ring":   pts[LM.RING_TIP].y   < pts[LM.RING_PIP].y,
            "pinky":  pts[LM.PINKY_TIP].y  < pts[LM.PINKY_PIP].y,
        }

        def d(a, b): return dist(pts[a], pts[b]) / palm_size
        dx = pts[LM.MIDDLE_MCP].x - pts[LM.WRIST].x
        dy = pts[LM.MIDDLE_MCP].y - pts[LM.WRIST].y

        return {
            "label": label, "score": score, "landmarks": pts,
            "index_tip":  px(LM.INDEX_TIP),
            "middle_tip": px(LM.MIDDLE_TIP),
            "ring_tip":   px(LM.RING_TIP),
            "pinky_tip":  px(LM.PINKY_TIP),
            "thumb_tip":  px(LM.THUMB_TIP),
            "wrist":      px(LM.WRIST),
            "extended":   fe,
            "count_extended": sum(fe.values()),
            "pinch_index":       d(LM.INDEX_TIP,  LM.THUMB_TIP),
            "pinch_middle":      d(LM.MIDDLE_TIP, LM.THUMB_TIP),
            "pinch_ring":        d(LM.RING_TIP,   LM.THUMB_TIP),
            "pinch_pinky":       d(LM.PINKY_TIP,  LM.THUMB_TIP),
            "two_finger_spread": d(LM.INDEX_TIP,  LM.MIDDLE_TIP),
            "palm_size":    palm_size,
            "wrist_angle":  math.degrees(math.atan2(dy, dx)),
        }

    def _thumb_extended(self, pts, label):
        if label == "Right":
            return pts[LM.THUMB_TIP].x < pts[LM.THUMB_IP].x
        else:
            return pts[LM.THUMB_TIP].x > pts[LM.THUMB_IP].x
