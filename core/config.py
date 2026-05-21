"""
config.py — Persistent configuration management for GestureControl.
Handles loading/saving user settings and gesture bindings.
"""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gesture_config.json")

# ── Default gesture-to-action bindings ─────────────────────────────────────────
DEFAULT_GESTURES = {
    # ── CURSOR CONTROL ──────────────────────────────────────────────────────────
    "index_tip_move": {
        "name": "Move Cursor",
        "description": "Point index finger — tip controls cursor like a touchpad",
        "action": "MOVE_CURSOR",
        "hand": "any",
        "icon": "☝️",
        "category": "cursor",
        "enabled": True,
        "editable": False,
    },

    # ── CLICKING ────────────────────────────────────────────────────────────────
    "pinch_index_thumb": {
        "name": "Left Click",
        "description": "Pinch index finger and thumb together",
        "action": "LEFT_CLICK",
        "hand": "any",
        "icon": "👌",
        "category": "click",
        "enabled": True,
        "editable": True,
    },
    "pinch_middle_thumb": {
        "name": "Right Click",
        "description": "Pinch middle finger and thumb together",
        "action": "RIGHT_CLICK",
        "hand": "any",
        "icon": "🤌",
        "category": "click",
        "enabled": True,
        "editable": True,
    },
    "double_pinch_index_thumb": {
        "name": "Double Click",
        "description": "Quick double pinch — index finger and thumb",
        "action": "DOUBLE_CLICK",
        "hand": "any",
        "icon": "✌️",
        "category": "click",
        "enabled": True,
        "editable": True,
    },
    "pinch_ring_thumb": {
        "name": "Middle Click",
        "description": "Pinch ring finger and thumb",
        "action": "MIDDLE_CLICK",
        "hand": "any",
        "icon": "🖖",
        "category": "click",
        "enabled": True,
        "editable": True,
    },

    # ── DRAG ────────────────────────────────────────────────────────────────────
    "pinch_hold_move": {
        "name": "Click & Drag",
        "description": "Pinch index+thumb and hold while moving hand",
        "action": "DRAG",
        "hand": "any",
        "icon": "🫳",
        "category": "drag",
        "enabled": True,
        "editable": True,
    },

    # ── SCROLLING ───────────────────────────────────────────────────────────────
    "two_finger_swipe_up": {
        "name": "Scroll Up",
        "description": "Raise index + middle fingers, swipe up",
        "action": "SCROLL_UP",
        "hand": "any",
        "icon": "🖖",
        "category": "scroll",
        "enabled": True,
        "editable": True,
    },
    "two_finger_swipe_down": {
        "name": "Scroll Down",
        "description": "Raise index + middle fingers, swipe down",
        "action": "SCROLL_DOWN",
        "hand": "any",
        "icon": "🖖",
        "category": "scroll",
        "enabled": True,
        "editable": True,
    },
    "two_finger_swipe_left": {
        "name": "Scroll Left / Back",
        "description": "Raise index + middle fingers, swipe left",
        "action": "SCROLL_LEFT",
        "hand": "any",
        "icon": "⬅️",
        "category": "scroll",
        "enabled": True,
        "editable": True,
    },
    "two_finger_swipe_right": {
        "name": "Scroll Right / Forward",
        "description": "Raise index + middle fingers, swipe right",
        "action": "SCROLL_RIGHT",
        "hand": "any",
        "icon": "➡️",
        "category": "scroll",
        "enabled": True,
        "editable": True,
    },

    # ── ZOOM ────────────────────────────────────────────────────────────────────
    "pinch_spread": {
        "name": "Zoom In",
        "description": "Spread thumb and index finger apart",
        "action": "ZOOM_IN",
        "hand": "any",
        "icon": "🔍",
        "category": "zoom",
        "enabled": True,
        "editable": True,
    },
    "pinch_close": {
        "name": "Zoom Out",
        "description": "Bring thumb and index finger together",
        "action": "ZOOM_OUT",
        "hand": "any",
        "icon": "🔎",
        "category": "zoom",
        "enabled": True,
        "editable": True,
    },

    # ── WINDOW MANAGEMENT ───────────────────────────────────────────────────────
    "fist_closed": {
        "name": "Grab / Hold",
        "description": "Close all fingers into a fist — grab selected item",
        "action": "FIST_GRAB",
        "hand": "any",
        "icon": "✊",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "palm_swipe_left": {
        "name": "Virtual Desktop Left",
        "description": "Open palm, swipe left — switch to left virtual desktop",
        "action": "VIRTUAL_DESKTOP_LEFT",
        "hand": "any",
        "icon": "🫲",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "palm_swipe_right": {
        "name": "Virtual Desktop Right",
        "description": "Open palm, swipe right — switch to right virtual desktop",
        "action": "VIRTUAL_DESKTOP_RIGHT",
        "hand": "any",
        "icon": "🫱",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "palm_swipe_up": {
        "name": "Task View / Mission Control",
        "description": "Open palm, swipe up — open Windows Task View",
        "action": "TASK_VIEW",
        "hand": "any",
        "icon": "🫷",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "palm_swipe_down": {
        "name": "Show Desktop",
        "description": "Open palm, swipe down — minimize all windows",
        "action": "SHOW_DESKTOP",
        "hand": "any",
        "icon": "🖐️",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "three_finger_tap": {
        "name": "Action Center",
        "description": "Three fingers pointing up, tap — open Action Center",
        "action": "ACTION_CENTER",
        "hand": "any",
        "icon": "🤟",
        "category": "window",
        "enabled": True,
        "editable": True,
    },
    "four_finger_tap": {
        "name": "Alt+Tab",
        "description": "Four fingers pointing up, tap — switch app",
        "action": "ALT_TAB",
        "hand": "any",
        "icon": "🖐️",
        "category": "window",
        "enabled": True,
        "editable": True,
    },

    # ── MEDIA CONTROL ───────────────────────────────────────────────────────────
    "thumb_up": {
        "name": "Volume Up",
        "description": "Thumbs up gesture — increase volume",
        "action": "VOLUME_UP",
        "hand": "any",
        "icon": "👍",
        "category": "media",
        "enabled": True,
        "editable": True,
    },
    "thumb_down": {
        "name": "Volume Down",
        "description": "Thumbs down gesture — decrease volume",
        "action": "VOLUME_DOWN",
        "hand": "any",
        "icon": "👎",
        "category": "media",
        "enabled": True,
        "editable": True,
    },
    "ok_sign": {
        "name": "Play / Pause",
        "description": "OK sign (index+thumb circle, others extended) — play/pause media",
        "action": "PLAY_PAUSE",
        "hand": "any",
        "icon": "👌",
        "category": "media",
        "enabled": True,
        "editable": True,
    },
    "two_finger_right_swipe_quick": {
        "name": "Next Track",
        "description": "Quick two-finger swipe right — next media track",
        "action": "NEXT_TRACK",
        "hand": "any",
        "icon": "⏭️",
        "category": "media",
        "enabled": True,
        "editable": True,
    },
    "two_finger_left_swipe_quick": {
        "name": "Previous Track",
        "description": "Quick two-finger swipe left — previous media track",
        "action": "PREV_TRACK",
        "hand": "any",
        "icon": "⏮️",
        "category": "media",
        "enabled": True,
        "editable": True,
    },

    # ── BROWSER / APP ───────────────────────────────────────────────────────────
    "l_shape": {
        "name": "New Tab",
        "description": "L-shape with thumb and index — open new browser tab",
        "action": "NEW_TAB",
        "hand": "any",
        "icon": "🖖",
        "category": "browser",
        "enabled": True,
        "editable": True,
    },
    "x_fingers_cross": {
        "name": "Close Tab",
        "description": "Cross index and middle fingers — close current tab",
        "action": "CLOSE_TAB",
        "hand": "any",
        "icon": "❌",
        "category": "browser",
        "enabled": True,
        "editable": True,
    },
    "five_finger_spread": {
        "name": "Close Window",
        "description": "Spread all five fingers wide — close active window",
        "action": "CLOSE_WINDOW",
        "hand": "any",
        "icon": "✋",
        "category": "browser",
        "enabled": True,
        "editable": True,
    },
    "shake_hand": {
        "name": "Undo",
        "description": "Shake hand left-right — Ctrl+Z undo",
        "action": "UNDO",
        "hand": "any",
        "icon": "🫱",
        "category": "browser",
        "enabled": True,
        "editable": True,
    },
    "snap_fingers": {
        "name": "Screenshot",
        "description": "Snap motion (middle+thumb flick) — take screenshot",
        "action": "SCREENSHOT",
        "hand": "any",
        "icon": "📸",
        "category": "browser",
        "enabled": True,
        "editable": True,
    },

    # ── ADVANCED / AI FEATURES ──────────────────────────────────────────────────
    "write_in_air": {
        "name": "Air Writing (Experimental)",
        "description": "Trace letters with index finger tip in the air — text input",
        "action": "AIR_WRITE",
        "hand": "any",
        "icon": "✍️",
        "category": "advanced",
        "enabled": False,
        "editable": True,
    },
    "draw_circle": {
        "name": "Rotate / Spin",
        "description": "Draw a circle in the air — rotate selected object",
        "action": "ROTATE",
        "hand": "any",
        "icon": "🔄",
        "category": "advanced",
        "enabled": True,
        "editable": True,
    },
    "wrist_tilt_left": {
        "name": "Tilt / Rotate Left",
        "description": "Tilt wrist counter-clockwise — rotate selection left",
        "action": "TILT_LEFT",
        "hand": "any",
        "icon": "↩️",
        "category": "advanced",
        "enabled": True,
        "editable": True,
    },
    "wrist_tilt_right": {
        "name": "Tilt / Rotate Right",
        "description": "Tilt wrist clockwise — rotate selection right",
        "action": "TILT_RIGHT",
        "hand": "any",
        "icon": "↪️",
        "category": "advanced",
        "enabled": True,
        "editable": True,
    },
}

# ── Default settings ─────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "camera_index": 0,
    "cursor_smoothing": 7,          # 1=raw, 10=very smooth
    "cursor_sensitivity": 5,        # 1=slow, 10=fast
    "click_threshold": 0.04,        # pinch distance threshold (fraction of hand size)
    "scroll_speed": 3,              # scroll lines per gesture unit
    "zoom_speed": 3,
    "gesture_hold_ms": 150,         # ms before gesture is confirmed
    "pinch_hold_ms": 300,           # ms to hold pinch for drag
    "show_landmarks": True,         # show skeleton on preview
    "show_fps": True,
    "min_detection_confidence": 0.75,
    "min_tracking_confidence": 0.75,
    "dominant_hand": "right",       # "right" | "left" | "auto"
    "enable_both_hands": True,
    "mirror_camera": True,
    "active": False,                # gesture control on/off
    "start_minimized": False,
    "theme": "dark",                # "dark" | "light"
}


def load_config():
    """Load config from disk, falling back to defaults for missing keys."""
    if not os.path.exists(CONFIG_PATH):
        return {"settings": DEFAULT_SETTINGS.copy(), "gestures": DEFAULT_GESTURES.copy()}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults (add any new keys from defaults)
        settings = {**DEFAULT_SETTINGS, **data.get("settings", {})}
        gestures = {**DEFAULT_GESTURES, **data.get("gestures", {})}
        return {"settings": settings, "gestures": gestures}
    except Exception:
        return {"settings": DEFAULT_SETTINGS.copy(), "gestures": DEFAULT_GESTURES.copy()}


def save_config(config: dict):
    """Persist config to disk."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def reset_config():
    """Reset to factory defaults."""
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    return {"settings": DEFAULT_SETTINGS.copy(), "gestures": DEFAULT_GESTURES.copy()}
