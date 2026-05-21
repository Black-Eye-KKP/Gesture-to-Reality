"""
controller.py — Main controller that connects all components together.
Manages the tracking thread, gesture engine, and action executor.
"""

import threading
import time
from core.tracker import HandTracker
from core.gesture_engine import GestureEngine
from core.action_executor import ActionExecutor


class GestureController:
    """
    Top-level controller. Start/stop gesture recognition.
    The UI talks to this object exclusively.
    """

    def __init__(self, config: dict, on_frame=None, on_action=None, on_status=None):
        self.config = config
        self.settings = config["settings"]
        self.gestures = config["gestures"]
        self.on_frame = on_frame       # callback(frame_bgr, hands_data)
        self.on_action = on_action     # callback(action_name)
        self.on_status = on_status     # callback(status_str)

        self._running = False
        self._tracker = None
        self._engine = None
        self._executor = None
        self._frame_thread = None
        self._active = False           # gesture control ON/OFF (independent of running)

        self.fps = 0
        self._fps_times = []

    def start(self):
        """Start camera + tracking. Gestures only fire if activate() is called."""
        if self._running:
            return
        self._running = True
        self._active = self.settings.get("active", False)

        self._executor = ActionExecutor(
            self.settings,
            on_action=self._handle_action_feedback
        )
        self._engine = GestureEngine(
            self.settings,
            self.gestures,
            action_handler=self._route_action
        )
        self._tracker = HandTracker(
            self.settings,
            on_frame=self._on_raw_frame
        )

        try:
            self._tracker.start()
            if self.on_status:
                self.on_status("Camera started — gesture control ready")
        except Exception as e:
            self._running = False
            if self.on_status:
                self.on_status(f"Error: {e}")
            raise

    def stop(self):
        self._running = False
        self._active = False
        if self._tracker:
            self._tracker.stop()
            self._tracker = None
        if self.on_status:
            self.on_status("Stopped")

    def activate(self):
        """Turn on gesture → action routing."""
        self._active = True
        self.settings["active"] = True
        if self.on_status:
            self.on_status("Gesture control ACTIVE")

    def deactivate(self):
        """Pause gesture actions (tracking still runs for preview)."""
        self._active = False
        self.settings["active"] = False
        if self.on_status:
            self.on_status("Gesture control PAUSED")

    def toggle(self):
        if self._active:
            self.deactivate()
        else:
            self.activate()

    @property
    def is_running(self):
        return self._running

    @property
    def is_active(self):
        return self._active

    def update_settings(self, new_settings: dict):
        self.settings.update(new_settings)
        if self._engine:
            self._engine.settings = self.settings
        if self._executor:
            self._executor.settings = self.settings

    def update_gestures(self, new_gestures: dict):
        self.gestures.update(new_gestures)
        if self._engine:
            self._engine.gestures = self.gestures

    def _on_raw_frame(self, frame, hands_data):
        """Called by HandTracker each frame."""
        # FPS calculation
        now = time.time()
        self._fps_times = [t for t in self._fps_times if now - t < 1.0]
        self._fps_times.append(now)
        self.fps = len(self._fps_times)

        # Feed to gesture engine
        if self._engine:
            self._engine.update(hands_data)

        # Forward frame to UI
        if self.on_frame:
            self.on_frame(frame, hands_data)

    def _route_action(self, action: str, **kwargs):
        """Only pass actions to executor when gesture control is active."""
        if self._active and self._executor:
            self._executor.handle(action, **kwargs)
        # Always notify UI (for live gesture display)
        if self.on_action:
            self.on_action(action)

    def _handle_action_feedback(self, action: str):
        pass  # executor-level feedback (already handled above)
