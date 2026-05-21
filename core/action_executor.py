"""
action_executor.py — Translates gesture action names to actual Windows input.
Uses pyautogui for mouse/keyboard and pynput for low-level key combos.
"""

import time
import threading

PYAUTO_OK = False
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    PYAUTO_OK = True
except Exception:
    pass

try:
    import screeninfo
except Exception:
    screeninfo = None

try:
    from pynput.keyboard import Key, Controller as KbController
    PYNPUT_OK = True
    _kb = KbController()
except Exception:
    PYNPUT_OK = False
    _kb = None

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_OK = True
except Exception:
    PYCAW_OK = False


def _get_screen_size():
    try:
        if screeninfo is not None:
            screens = screeninfo.get_monitors()
            if screens:
                return screens[0].width, screens[0].height
    except Exception:
        pass
    try:
        import tkinter as _tk
        r = _tk.Tk(); r.withdraw()
        w, h = r.winfo_screenwidth(), r.winfo_screenheight()
        r.destroy()
        return w, h
    except Exception:
        pass
    return 1920, 1080


class ActionExecutor:
    """
    Receives action names from GestureEngine and performs the actual
    mouse/keyboard operation on Windows.
    """

    def __init__(self, settings: dict, on_action=None):
        self.settings = settings
        self.on_action = on_action     # callback for UI feedback (action name)
        self._sw, self._sh = _get_screen_size()
        self._dragging = False
        self._last_move = (0, 0)
        self._move_lock = threading.Lock()
        # Volume cache
        self._vol_interface = None
        self._init_volume()

    def handle(self, action: str, **kwargs):
        """Dispatch an action."""
        if self.on_action:
            self.on_action(action)

        if not PYAUTO_OK:
            return  # can't do anything without pyautogui

        try:
            fn = getattr(self, f"_do_{action.lower()}", None)
            if fn:
                fn(**kwargs)
            else:
                print(f"[ActionExecutor] Unknown action: {action}")
        except Exception as e:
            print(f"[ActionExecutor] Error executing {action}: {e}")

    # ─── CURSOR ─────────────────────────────────────────────────────────────────

    def _do_move_cursor(self, x, y, sensitivity=1.0, **_):
        """Map normalized (0-1) camera coords to screen pixels."""
        # Invert y because camera y=0 is top
        # Apply sensitivity scaling around center
        cx = 0.5 + (x - 0.5) * sensitivity
        cy = 0.5 + (y - 0.5) * sensitivity
        # Clamp
        cx = max(0.01, min(0.99, cx))
        cy = max(0.01, min(0.99, cy))

        px = int(cx * self._sw)
        py = int(cy * self._sh)

        with self._move_lock:
            pyautogui.moveTo(px, py, _pause=False)
            self._last_move = (px, py)

    # ─── CLICKS ─────────────────────────────────────────────────────────────────

    def _do_left_click(self, **_):
        pyautogui.click()

    def _do_right_click(self, **_):
        pyautogui.rightClick()

    def _do_double_click(self, **_):
        pyautogui.doubleClick()

    def _do_middle_click(self, **_):
        pyautogui.middleClick()

    # ─── DRAG ───────────────────────────────────────────────────────────────────

    def _do_drag_start(self, **_):
        pyautogui.mouseDown()
        self._dragging = True

    def _do_drag(self, x, y, **_):
        if self._dragging:
            px = int(x * self._sw)
            py = int(y * self._sh)
            pyautogui.moveTo(px, py, _pause=False)

    def _do_drag_end(self, **_):
        pyautogui.mouseUp()
        self._dragging = False

    def _do_fist_grab(self, **_):
        pass  # context-sensitive; defaults to no-op

    # ─── SCROLL ─────────────────────────────────────────────────────────────────

    def _do_scroll_up(self, amount=3, **_):
        pyautogui.scroll(amount)

    def _do_scroll_down(self, amount=3, **_):
        pyautogui.scroll(-amount)

    def _do_scroll_left(self, amount=3, **_):
        pyautogui.hscroll(-amount)

    def _do_scroll_right(self, amount=3, **_):
        pyautogui.hscroll(amount)

    # ─── ZOOM ───────────────────────────────────────────────────────────────────

    def _do_zoom_in(self, factor=1.1, **_):
        pyautogui.hotkey("ctrl", "+")

    def _do_zoom_out(self, factor=1.1, **_):
        pyautogui.hotkey("ctrl", "-")

    def _do_rotate(self, **_):
        pass  # app-specific; placeholder

    def _do_tilt_left(self, **_):
        pyautogui.hotkey("ctrl", "z")  # undo as rotate-left placeholder

    def _do_tilt_right(self, **_):
        pyautogui.hotkey("ctrl", "y")

    # ─── WINDOW MANAGEMENT ──────────────────────────────────────────────────────

    def _do_virtual_desktop_left(self, **_):
        pyautogui.hotkey("ctrl", "win", "left")

    def _do_virtual_desktop_right(self, **_):
        pyautogui.hotkey("ctrl", "win", "right")

    def _do_task_view(self, **_):
        pyautogui.hotkey("win", "tab")

    def _do_show_desktop(self, **_):
        pyautogui.hotkey("win", "d")

    def _do_action_center(self, **_):
        pyautogui.hotkey("win", "a")

    def _do_alt_tab(self, **_):
        pyautogui.hotkey("alt", "tab")

    def _do_close_window(self, **_):
        pyautogui.hotkey("alt", "f4")

    def _do_close_tab(self, **_):
        pyautogui.hotkey("ctrl", "w")

    def _do_new_tab(self, **_):
        pyautogui.hotkey("ctrl", "t")

    def _do_undo(self, **_):
        pyautogui.hotkey("ctrl", "z")

    def _do_screenshot(self, **_):
        pyautogui.hotkey("win", "shift", "s")

    def _do_air_write(self, text="", **_):
        if text:
            pyautogui.typewrite(text, interval=0.05)

    # ─── MEDIA ──────────────────────────────────────────────────────────────────

    def _do_volume_up(self, **_):
        if PYCAW_OK and self._vol_interface:
            current = self._vol_interface.GetMasterVolumeLevelScalar()
            self._vol_interface.SetMasterVolumeLevelScalar(min(1.0, current + 0.05), None)
        else:
            pyautogui.press("volumeup")

    def _do_volume_down(self, **_):
        if PYCAW_OK and self._vol_interface:
            current = self._vol_interface.GetMasterVolumeLevelScalar()
            self._vol_interface.SetMasterVolumeLevelScalar(max(0.0, current - 0.05), None)
        else:
            pyautogui.press("volumedown")

    def _do_play_pause(self, **_):
        pyautogui.press("playpause")

    def _do_next_track(self, **_):
        pyautogui.press("nexttrack")

    def _do_prev_track(self, **_):
        pyautogui.press("prevtrack")

    # ─── BROWSER ────────────────────────────────────────────────────────────────

    def _do_scroll_left(self, amount=3, **_):
        try:
            pyautogui.hscroll(-amount)
        except Exception:
            pyautogui.hotkey("alt", "left")  # fallback: browser back

    def _do_scroll_right(self, amount=3, **_):
        try:
            pyautogui.hscroll(amount)
        except Exception:
            pyautogui.hotkey("alt", "right")  # fallback: browser forward

    # ─── VOLUME INIT ────────────────────────────────────────────────────────────

    def _init_volume(self):
        if not PYCAW_OK:
            return
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._vol_interface = cast(interface, POINTER(IAudioEndpointVolume))
        except Exception:
            self._vol_interface = None
