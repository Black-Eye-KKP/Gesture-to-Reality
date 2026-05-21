"""
gesture_engine.py — Converts raw hand-tracking data into high-level gesture events.
Implements smoothing, debouncing, velocity detection, and all gesture logic.
"""

import time
import math
from collections import deque


class GestureEngine:
    """
    Stateful gesture interpreter. Feed it hand_state dicts from the tracker
    and it fires action callbacks.
    """

    def __init__(self, settings: dict, gestures: dict, action_handler):
        self.settings = settings
        self.gestures = gestures
        self.action_handler = action_handler  # callable(action_name, **kwargs)

        # Cursor smoothing buffer
        smooth = max(1, settings.get("cursor_smoothing", 7))
        self._cursor_buf = deque(maxlen=smooth)
        self._last_cursor = (0.5, 0.5)

        # Gesture state machine
        self._pinch_state = {}        # hand_label -> {active, start_time, start_pos}
        self._scroll_state = {}       # hand_label -> {last_pos, velocity}
        self._gesture_cooldown = {}   # gesture_id -> last_fire_time
        self._shake_history = deque(maxlen=12)
        self._prev_hands = {}

        # Zoom: track two-hand or two-finger distance
        self._zoom_ref_dist = None
        self._last_zoom_time = 0

        # Double-click detection
        self._last_click_time = 0
        self._double_click_window = 0.35  # seconds

        # Velocity tracking per hand
        self._pos_history = {}   # label -> deque of (time, x, y)

    def update(self, hands_data: list):
        """Main update — call every frame with current hand list."""
        if not hands_data:
            self._cursor_buf.clear()
            self._pinch_state = {}
            return

        for hand in hands_data:
            label = hand["label"]
            if label not in self._pos_history:
                self._pos_history[label] = deque(maxlen=10)
            self._pos_history[label].append((time.time(), *hand["index_tip"]))

        # Primary hand (dominant or first detected)
        primary = self._get_primary_hand(hands_data)
        if primary:
            self._handle_cursor(primary)
            self._handle_clicks(primary)
            self._handle_scroll(primary, hands_data)
            self._handle_zoom(primary, hands_data)
            self._handle_window_gestures(primary)
            self._handle_media(primary)
            self._handle_shake(primary)
            self._handle_advanced(primary)

        self._prev_hands = {h["label"]: h for h in hands_data}

    def _get_primary_hand(self, hands):
        dom = self.settings.get("dominant_hand", "right").capitalize()
        for h in hands:
            if h["label"] == dom:
                return h
        return hands[0] if hands else None

    # ─── CURSOR ─────────────────────────────────────────────────────────────────

    def _handle_cursor(self, hand):
        """Move cursor based on index fingertip — smooth like a touchpad."""
        if not self._gesture_enabled("index_tip_move"):
            return

        ix, iy = hand["index_tip"]
        self._cursor_buf.append((ix, iy))

        # Weighted average (more weight to recent)
        if not self._cursor_buf:
            return
        weights = [i + 1 for i in range(len(self._cursor_buf))]
        wx = sum(p[0] * w for p, w in zip(self._cursor_buf, weights)) / sum(weights)
        wy = sum(p[1] * w for p, w in zip(self._cursor_buf, weights)) / sum(weights)

        sens = self.settings.get("cursor_sensitivity", 5) / 5.0
        # Map from camera space to screen (with deadzone in center)
        self._last_cursor = (wx, wy)
        self.action_handler("MOVE_CURSOR", x=wx, y=wy, sensitivity=sens)

    # ─── CLICKS ─────────────────────────────────────────────────────────────────

    def _handle_clicks(self, hand):
        label = hand["label"]
        thresh = self.settings.get("click_threshold", 0.04)
        hold_ms = self.settings.get("pinch_hold_ms", 300)
        now = time.time()

        pinching_index = hand["pinch_index"] < thresh
        pinching_middle = hand["pinch_middle"] < thresh
        pinching_ring = hand["pinch_ring"] < thresh

        state = self._pinch_state.get(label, {"active": False, "finger": None,
                                               "start_time": 0, "start_pos": None,
                                               "dragging": False})

        if pinching_index and not state["active"]:
            # Started pinching index
            state = {"active": True, "finger": "index",
                     "start_time": now, "start_pos": hand["index_tip"],
                     "dragging": False}
            self._pinch_state[label] = state

        elif pinching_middle and not state["active"]:
            state = {"active": True, "finger": "middle",
                     "start_time": now, "start_pos": hand["middle_tip"],
                     "dragging": False}
            self._pinch_state[label] = state

        elif pinching_ring and not state["active"]:
            state = {"active": True, "finger": "ring",
                     "start_time": now, "start_pos": hand["ring_tip"],
                     "dragging": False}
            self._pinch_state[label] = state

        elif state["active"]:
            finger = state["finger"]
            still_pinching = (
                (finger == "index" and pinching_index) or
                (finger == "middle" and pinching_middle) or
                (finger == "ring" and pinching_ring)
            )
            held_duration = (now - state["start_time"]) * 1000

            if still_pinching:
                # Check for drag start
                if finger == "index" and held_duration > hold_ms and not state["dragging"]:
                    state["dragging"] = True
                    self.action_handler("DRAG_START")
                elif state["dragging"]:
                    self.action_handler("DRAG", x=hand["index_tip"][0], y=hand["index_tip"][1])

            else:
                # Released
                if state["dragging"]:
                    self.action_handler("DRAG_END")
                elif finger == "index" and self._gesture_enabled("pinch_index_thumb"):
                    # Check double-click
                    if (now - self._last_click_time) < self._double_click_window:
                        self.action_handler("DOUBLE_CLICK")
                        self._last_click_time = 0
                    else:
                        self.action_handler("LEFT_CLICK")
                        self._last_click_time = now
                elif finger == "middle" and self._gesture_enabled("pinch_middle_thumb"):
                    self.action_handler("RIGHT_CLICK")
                elif finger == "ring" and self._gesture_enabled("pinch_ring_thumb"):
                    self.action_handler("MIDDLE_CLICK")

                state = {"active": False, "finger": None,
                         "start_time": 0, "start_pos": None, "dragging": False}

            self._pinch_state[label] = state

    # ─── SCROLL ─────────────────────────────────────────────────────────────────

    def _handle_scroll(self, hand, all_hands):
        ext = hand["extended"]
        # Two-finger scroll: index + middle extended, others curled
        if not (ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"]):
            self._scroll_state.pop(hand["label"], None)
            return

        label = hand["label"]
        tip_x = (hand["index_tip"][0] + hand["middle_tip"][0]) / 2
        tip_y = (hand["index_tip"][1] + hand["middle_tip"][1]) / 2

        if label not in self._scroll_state:
            self._scroll_state[label] = {"last_pos": (tip_x, tip_y), "last_time": time.time()}
            return

        prev = self._scroll_state[label]
        dx = tip_x - prev["last_pos"][0]
        dy = tip_y - prev["last_pos"][1]
        dt = time.time() - prev["last_time"]

        speed = self.settings.get("scroll_speed", 3)
        threshold = 0.008

        if abs(dy) > abs(dx):
            if dy < -threshold and self._gesture_enabled("two_finger_swipe_up"):
                self.action_handler("SCROLL_UP", amount=int(abs(dy) / 0.01 * speed))
            elif dy > threshold and self._gesture_enabled("two_finger_swipe_down"):
                self.action_handler("SCROLL_DOWN", amount=int(abs(dy) / 0.01 * speed))
        else:
            if dx < -threshold and self._gesture_enabled("two_finger_swipe_left"):
                self.action_handler("SCROLL_LEFT", amount=int(abs(dx) / 0.01 * speed))
            elif dx > threshold and self._gesture_enabled("two_finger_swipe_right"):
                self.action_handler("SCROLL_RIGHT", amount=int(abs(dx) / 0.01 * speed))

        self._scroll_state[label] = {"last_pos": (tip_x, tip_y), "last_time": time.time()}

    # ─── ZOOM ───────────────────────────────────────────────────────────────────

    def _handle_zoom(self, hand, all_hands):
        now = time.time()
        if now - self._last_zoom_time < 0.1:
            return

        # Single-hand pinch-spread zoom (index+thumb, others curled)
        ext = hand["extended"]
        if not ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
            cur_dist = hand["pinch_index"]
            if self._zoom_ref_dist is None:
                self._zoom_ref_dist = cur_dist
            else:
                delta = self._zoom_ref_dist - cur_dist
                speed = self.settings.get("zoom_speed", 3)
                if delta > 0.05 and self._gesture_enabled("pinch_spread"):
                    self.action_handler("ZOOM_IN", factor=1 + delta * speed)
                    self._last_zoom_time = now
                    self._zoom_ref_dist = cur_dist
                elif delta < -0.05 and self._gesture_enabled("pinch_close"):
                    self.action_handler("ZOOM_OUT", factor=1 + abs(delta) * speed)
                    self._last_zoom_time = now
                    self._zoom_ref_dist = cur_dist
        else:
            self._zoom_ref_dist = None

    # ─── WINDOW MANAGEMENT ──────────────────────────────────────────────────────

    def _handle_window_gestures(self, hand):
        ext = hand["extended"]
        count = hand["count_extended"]
        label = hand["label"]

        # Palm open (all 5 extended)
        if count == 5:
            self._maybe_fire("palm_open", self._detect_palm_swipe, hand)

        # Fist
        elif count == 0:
            self._cooldown_fire("fist_closed", "FIST_GRAB", min_interval=1.0)

        # 3-finger tap
        elif count == 3 and ext["index"] and ext["middle"] and ext["ring"]:
            self._cooldown_fire("three_finger_tap", "ACTION_CENTER", min_interval=1.5)

        # 4-finger tap
        elif count == 4 and ext["index"] and ext["middle"] and ext["ring"] and ext["pinky"]:
            self._cooldown_fire("four_finger_tap", "ALT_TAB", min_interval=1.0)

        # All 5 spread fast for close window
        if count == 5 and self._gesture_enabled("five_finger_spread"):
            vel = self._get_velocity(label)
            if vel and vel > 0.03:
                self._cooldown_fire("five_finger_spread", "CLOSE_WINDOW", min_interval=2.0)

        # L-shape: only index + thumb extended
        if ext["index"] and ext["thumb"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
            self._cooldown_fire("l_shape", "NEW_TAB", min_interval=1.5)

        # Cross fingers (index over middle)
        if count == 2 and ext["index"] and ext["middle"]:
            ix, _ = hand["index_tip"]
            mx, _ = hand["middle_tip"]
            if abs(ix - mx) < 0.02:  # very close together = crossed
                self._cooldown_fire("x_fingers_cross", "CLOSE_TAB", min_interval=1.5)

    def _detect_palm_swipe(self, hand):
        label = hand["label"]
        vel_x, vel_y = self._get_velocity_xy(label) or (0, 0)
        spd = self.settings.get("scroll_speed", 3)
        if vel_x < -0.02:
            self._cooldown_fire("palm_swipe_left", "VIRTUAL_DESKTOP_LEFT", 1.5)
        elif vel_x > 0.02:
            self._cooldown_fire("palm_swipe_right", "VIRTUAL_DESKTOP_RIGHT", 1.5)
        elif vel_y < -0.02:
            self._cooldown_fire("palm_swipe_up", "TASK_VIEW", 1.5)
        elif vel_y > 0.02:
            self._cooldown_fire("palm_swipe_down", "SHOW_DESKTOP", 1.5)

    # ─── MEDIA ──────────────────────────────────────────────────────────────────

    def _handle_media(self, hand):
        ext = hand["extended"]
        count = hand["count_extended"]

        # Thumbs up: only thumb extended, pointing up (thumb tip above wrist)
        if ext["thumb"] and count == 1:
            wrist_y = hand["wrist"][1]
            thumb_y = hand["thumb_tip"][1]
            if thumb_y < wrist_y - 0.05:
                self._cooldown_fire("thumb_up", "VOLUME_UP", 0.5)
            elif thumb_y > wrist_y + 0.05:
                self._cooldown_fire("thumb_down", "VOLUME_DOWN", 0.5)

        # OK sign: index+thumb form circle, middle+ring+pinky extended
        if ext["middle"] and ext["ring"] and ext["pinky"] and not ext["index"]:
            if hand["pinch_index"] < 0.15:  # index tip near thumb
                self._cooldown_fire("ok_sign", "PLAY_PAUSE", 1.5)

        # Quick two-finger swipes for track control
        if ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"]:
            label = hand["label"]
            vel_x, _ = self._get_velocity_xy(label) or (0, 0)
            if vel_x > 0.05:
                self._cooldown_fire("two_finger_right_swipe_quick", "NEXT_TRACK", 1.0)
            elif vel_x < -0.05:
                self._cooldown_fire("two_finger_left_swipe_quick", "PREV_TRACK", 1.0)

    # ─── ADVANCED ───────────────────────────────────────────────────────────────

    def _handle_shake(self, hand):
        label = hand["label"]
        vel_x, _ = self._get_velocity_xy(label) or (0, 0)
        now = time.time()
        self._shake_history.append((now, vel_x))

        # Detect oscillating x velocity (shake)
        if len(self._shake_history) >= 8:
            recent = [v for t, v in self._shake_history if now - t < 0.8]
            if len(recent) >= 6:
                sign_changes = sum(1 for i in range(1, len(recent))
                                   if recent[i] * recent[i-1] < 0 and abs(recent[i]) > 0.02)
                if sign_changes >= 3:
                    self._cooldown_fire("shake_hand", "UNDO", 2.0)
                    self._shake_history.clear()

    def _handle_advanced(self, hand):
        if not self._gesture_enabled("draw_circle"):
            return
        # Circle detection: track wrist path and check for circular motion
        label = hand["label"]
        hist = self._pos_history.get(label, deque())
        if len(hist) < 10:
            return
        pts = [(x, y) for _, x, y in hist]
        # Simple heuristic: check bounding box is roughly square and movement is non-trivial
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)
        if span_x > 0.05 and span_y > 0.05 and abs(span_x - span_y) / max(span_x, span_y) < 0.5:
            # Check if path closes on itself
            start = pts[0]
            end = pts[-1]
            closure = math.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
            if closure < 0.03:
                self._cooldown_fire("draw_circle", "ROTATE", 2.0)

    # ─── HELPERS ────────────────────────────────────────────────────────────────

    def _gesture_enabled(self, gesture_id):
        g = self.gestures.get(gesture_id, {})
        return g.get("enabled", True)

    def _cooldown_fire(self, gesture_id, action, min_interval=1.0, **kwargs):
        if not self._gesture_enabled(gesture_id):
            return
        now = time.time()
        last = self._gesture_cooldown.get(gesture_id, 0)
        if now - last >= min_interval:
            self._gesture_cooldown[gesture_id] = now
            self.action_handler(action, **kwargs)

    def _maybe_fire(self, key, fn, *args):
        fn(*args)

    def _get_velocity(self, label):
        """Scalar speed of index tip."""
        vxy = self._get_velocity_xy(label)
        if vxy is None:
            return 0
        return math.sqrt(vxy[0]**2 + vxy[1]**2)

    def _get_velocity_xy(self, label):
        hist = self._pos_history.get(label)
        if not hist or len(hist) < 3:
            return None
        recent = list(hist)[-4:]
        if len(recent) < 2:
            return None
        dt = recent[-1][0] - recent[0][0]
        if dt < 1e-6:
            return None
        dx = (recent[-1][1] - recent[0][1]) / dt
        dy = (recent[-1][2] - recent[0][2]) / dt
        return dx, dy
