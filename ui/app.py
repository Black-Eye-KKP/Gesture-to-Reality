"""
app.py — Main GUI application for GestureControl.
Built with customtkinter for a modern Windows 11 look.
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    CTK_OK = True
except ImportError:
    CTK_OK = False

try:
    from PIL import Image, ImageTk
    import cv2
    import numpy as np
    PIL_OK = True
except ImportError:
    PIL_OK = False

from core.controller import GestureController
from core.config import load_config, save_config, reset_config, DEFAULT_GESTURES


CATEGORIES = {
    "cursor":  ("Cursor Control",    "🖱️"),
    "click":   ("Click Actions",     "👆"),
    "scroll":  ("Scroll",            "📜"),
    "zoom":    ("Zoom",              "🔍"),
    "drag":    ("Drag & Drop",       "✋"),
    "window":  ("Window Management", "🪟"),
    "media":   ("Media Control",     "🎵"),
    "browser": ("Browser & Apps",    "🌐"),
    "advanced":("Advanced / AI",     "🤖"),
}

ACTION_LIST = [
    "MOVE_CURSOR", "LEFT_CLICK", "RIGHT_CLICK", "DOUBLE_CLICK", "MIDDLE_CLICK",
    "DRAG", "DRAG_START", "DRAG_END", "SCROLL_UP", "SCROLL_DOWN",
    "SCROLL_LEFT", "SCROLL_RIGHT", "ZOOM_IN", "ZOOM_OUT", "ROTATE",
    "TILT_LEFT", "TILT_RIGHT", "FIST_GRAB", "VIRTUAL_DESKTOP_LEFT",
    "VIRTUAL_DESKTOP_RIGHT", "TASK_VIEW", "SHOW_DESKTOP", "ACTION_CENTER",
    "ALT_TAB", "CLOSE_WINDOW", "CLOSE_TAB", "NEW_TAB", "UNDO", "SCREENSHOT",
    "VOLUME_UP", "VOLUME_DOWN", "PLAY_PAUSE", "NEXT_TRACK", "PREV_TRACK",
    "AIR_WRITE",
]


class GestureControlApp:
    def __init__(self):
        if not CTK_OK:
            raise ImportError("customtkinter not installed. Run: pip install customtkinter")

        self.config = load_config()
        self.controller = GestureController(
            self.config,
            on_frame=self._on_frame,
            on_action=self._on_action,
            on_status=self._on_status,
        )

        self._last_frame = None
        self._last_action = ""
        self._action_time = 0
        self._frame_lock = threading.Lock()
        self._status_text = "Ready — press Start to begin"

        self._build_window()

    def run(self):
        self.root.mainloop()

    # ─── WINDOW SETUP ────────────────────────────────────────────────────────────

    def _build_window(self):
        self.root = ctk.CTk()
        self.root.title("GestureControl  ·  Hand Gesture Mouse")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Main content area
        self.content = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        # Build pages
        self.pages = {}
        self._build_page_dashboard()
        self._build_page_gestures()
        self._build_page_settings()
        self._build_page_help()

        self._show_page("dashboard")
        self._start_ui_update()

    def _build_sidebar(self):
        # Logo
        logo = ctk.CTkLabel(self.sidebar, text="✋ GestureControl",
                             font=ctk.CTkFont(size=17, weight="bold"))
        logo.pack(pady=(24, 8), padx=12)

        version = ctk.CTkLabel(self.sidebar, text="v1.0 · Windows 11",
                                font=ctk.CTkFont(size=11), text_color="gray")
        version.pack(pady=(0, 20))

        # Nav buttons
        self._nav_buttons = {}
        pages = [
            ("dashboard", "🏠  Dashboard"),
            ("gestures",  "🤌  Gestures"),
            ("settings",  "⚙️   Settings"),
            ("help",      "❓  Help"),
        ]
        for page_id, label in pages:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                fg_color="transparent", hover_color=("#3a3a3a", "#2a2a2a"),
                font=ctk.CTkFont(size=13),
                command=lambda p=page_id: self._show_page(p)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[page_id] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(
            fill="x", padx=16, pady=16)

        # Big toggle button
        self.toggle_btn = ctk.CTkButton(
            self.sidebar, text="▶  Start", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a7a3a", hover_color="#145f2d",
            command=self._toggle_controller
        )
        self.toggle_btn.pack(fill="x", padx=12, pady=4)

        self.active_btn = ctk.CTkButton(
            self.sidebar, text="⏸  Pause Gestures", height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#555", hover_color="#444",
            command=self._toggle_active,
            state="disabled"
        )
        self.active_btn.pack(fill="x", padx=12, pady=4)

        # Status
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(
            fill="x", padx=16, pady=12)
        self.status_label = ctk.CTkLabel(
            self.sidebar, text="● Stopped", text_color="gray",
            font=ctk.CTkFont(size=11), wraplength=170)
        self.status_label.pack(padx=12, pady=4)

        self.fps_label = ctk.CTkLabel(
            self.sidebar, text="FPS: —",
            font=ctk.CTkFont(size=11), text_color="gray")
        self.fps_label.pack(padx=12, pady=2)

    def _show_page(self, page_id):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[page_id].pack(fill="both", expand=True)
        # Highlight active nav
        for pid, btn in self._nav_buttons.items():
            btn.configure(fg_color="#1f538d" if pid == page_id else "transparent")

    # ─── DASHBOARD PAGE ──────────────────────────────────────────────────────────

    def _build_page_dashboard(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["dashboard"] = page

        ctk.CTkLabel(page, text="Dashboard",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 16))

        # Two columns
        cols = ctk.CTkFrame(page, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # Camera preview
        cam_card = ctk.CTkFrame(left, corner_radius=12)
        cam_card.pack(fill="both", expand=True, pady=(0, 12))
        ctk.CTkLabel(cam_card, text="Camera Preview",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.cam_label = ctk.CTkLabel(cam_card, text="Camera not started",
                                      fg_color="#1a1a2e", corner_radius=8)
        self.cam_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Last action display
        action_card = ctk.CTkFrame(left, corner_radius=12, height=70)
        action_card.pack(fill="x", pady=(0, 0))
        action_card.pack_propagate(False)
        ctk.CTkLabel(action_card, text="Last Gesture",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=16, pady=(8, 0))
        self.action_label = ctk.CTkLabel(action_card, text="—",
                                          font=ctk.CTkFont(size=18, weight="bold"),
                                          text_color="#4fc3f7")
        self.action_label.pack(anchor="w", padx=16)

        # Right: hand info + quick guide
        info_card = ctk.CTkFrame(right, corner_radius=12)
        info_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(info_card, text="Hand Detection",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))

        self.hand_info_label = ctk.CTkLabel(info_card, text="No hands detected",
                                             font=ctk.CTkFont(size=12), text_color="gray",
                                             justify="left")
        self.hand_info_label.pack(anchor="w", padx=16, pady=(0, 12))

        # Quick reference
        ref_card = ctk.CTkFrame(right, corner_radius=12)
        ref_card.pack(fill="both", expand=True)
        ctk.CTkLabel(ref_card, text="Quick Reference",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(12, 8))

        quick = [
            ("☝️ Point index finger",     "Move cursor"),
            ("👌 Pinch index + thumb",     "Left click"),
            ("🤌 Pinch middle + thumb",    "Right click"),
            ("✌️ Two fingers swipe",       "Scroll"),
            ("🤏 Spread index + thumb",    "Zoom in/out"),
            ("🖐️ Open palm swipe",        "Desktop / Apps"),
            ("👍 Thumb up",               "Volume up"),
            ("✊ Fist",                   "Grab"),
        ]
        for gesture, action in quick:
            row = ctk.CTkFrame(ref_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=1)
            ctk.CTkLabel(row, text=gesture, width=190,
                         font=ctk.CTkFont(size=12), anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=action,
                         font=ctk.CTkFont(size=12), text_color="gray", anchor="w").pack(side="left")

        ctk.CTkLabel(ref_card, text="→ See Gestures tab for all 30+ gestures",
                     font=ctk.CTkFont(size=11), text_color="#4fc3f7").pack(
                         anchor="w", padx=16, pady=(8, 12))

    # ─── GESTURES PAGE ───────────────────────────────────────────────────────────

    def _build_page_gestures(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["gestures"] = page

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="Gesture Editor",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Add Custom", width=120,
                      command=self._add_custom_gesture).pack(side="right")
        ctk.CTkButton(header, text="Reset All", width=100,
                      fg_color="#5a1a1a", hover_color="#7a2a2a",
                      command=self._reset_gestures).pack(side="right", padx=8)

        # Category filter
        filter_frame = ctk.CTkFrame(page, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(filter_frame, text="Category:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0,8))
        self._cat_var = ctk.StringVar(value="all")
        cats = [("All", "all")] + [(f"{v[1]} {v[0]}", k) for k, v in CATEGORIES.items()]
        self._cat_menu = ctk.CTkOptionMenu(filter_frame,
                                            values=[c[0] for c in cats],
                                            variable=self._cat_var,
                                            command=lambda _: self._refresh_gesture_list())
        self._cat_menu.pack(side="left")
        self._cat_options = cats

        # Scrollable gesture list
        self._gesture_scroll = ctk.CTkScrollableFrame(page, corner_radius=12)
        self._gesture_scroll.pack(fill="both", expand=True)
        self._gesture_rows = {}
        self._refresh_gesture_list()

    def _refresh_gesture_list(self):
        for w in self._gesture_scroll.winfo_children():
            w.destroy()
        self._gesture_rows.clear()

        selected_cat = self._cat_var.get()
        # Map display name back to key
        cat_key = "all"
        for name, key in self._cat_options:
            if name == selected_cat:
                cat_key = key
                break

        grouped = {}
        for gid, g in self.config["gestures"].items():
            cat = g.get("category", "advanced")
            if cat_key != "all" and cat != cat_key:
                continue
            grouped.setdefault(cat, []).append((gid, g))

        for cat, items in grouped.items():
            cat_name, cat_icon = CATEGORIES.get(cat, (cat, "•"))
            ctk.CTkLabel(self._gesture_scroll,
                         text=f"{cat_icon}  {cat_name}",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(
                             anchor="w", padx=8, pady=(12, 4))

            for gid, g in items:
                self._build_gesture_row(gid, g)

    def _build_gesture_row(self, gid, g):
        row = ctk.CTkFrame(self._gesture_scroll, corner_radius=8)
        row.pack(fill="x", padx=4, pady=3)

        # Enable toggle
        var = ctk.BooleanVar(value=g.get("enabled", True))
        switch = ctk.CTkSwitch(row, variable=var, text="",
                                width=44, command=lambda v=var, id=gid: self._toggle_gesture(id, v.get()))
        switch.pack(side="left", padx=(12, 8), pady=8)

        # Icon + name
        icon_label = ctk.CTkLabel(row, text=g.get("icon", "•"), font=ctk.CTkFont(size=18), width=30)
        icon_label.pack(side="left", padx=(0, 8))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=g.get("name", gid),
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=g.get("description", ""),
                     font=ctk.CTkFont(size=11), text_color="gray", anchor="w").pack(anchor="w")

        # Action badge
        action_label = ctk.CTkLabel(row, text=g.get("action", ""),
                                     font=ctk.CTkFont(size=11),
                                     fg_color="#1f3a5f", corner_radius=6,
                                     padx=8, pady=2)
        action_label.pack(side="right", padx=8)

        # Edit button (if editable)
        if g.get("editable", True):
            edit_btn = ctk.CTkButton(row, text="Edit", width=60, height=28,
                                      font=ctk.CTkFont(size=11),
                                      command=lambda id=gid: self._edit_gesture(id))
            edit_btn.pack(side="right", padx=4)

        self._gesture_rows[gid] = {"var": var, "row": row}

    def _toggle_gesture(self, gid, enabled):
        self.config["gestures"][gid]["enabled"] = enabled
        self.controller.update_gestures(self.config["gestures"])
        save_config(self.config)

    def _edit_gesture(self, gid):
        g = self.config["gestures"][gid]
        self._open_gesture_editor(gid, g)

    def _add_custom_gesture(self):
        new_id = f"custom_{int(time.time())}"
        new_g = {
            "name": "New Gesture",
            "description": "Describe your gesture here",
            "action": "LEFT_CLICK",
            "hand": "any",
            "icon": "✋",
            "category": "advanced",
            "enabled": True,
            "editable": True,
        }
        self.config["gestures"][new_id] = new_g
        save_config(self.config)
        self._open_gesture_editor(new_id, new_g)

    def _open_gesture_editor(self, gid, g):
        win = ctk.CTkToplevel(self.root)
        win.title(f"Edit: {g.get('name', gid)}")
        win.geometry("480x520")
        win.grab_set()

        ctk.CTkLabel(win, text="Edit Gesture",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 4), padx=20, anchor="w")
        ctk.CTkLabel(win, text=f"ID: {gid}",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(padx=20, anchor="w")

        fields = ctk.CTkFrame(win, fg_color="transparent")
        fields.pack(fill="both", expand=True, padx=20, pady=12)

        def field(label, default=""):
            ctk.CTkLabel(fields, text=label, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))
            e = ctk.CTkEntry(fields, height=36)
            e.insert(0, default)
            e.pack(fill="x")
            return e

        name_e = field("Gesture Name", g.get("name", ""))
        desc_e = field("Description", g.get("description", ""))
        icon_e = field("Icon (emoji)", g.get("icon", "✋"))

        ctk.CTkLabel(fields, text="Action", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))
        action_var = ctk.StringVar(value=g.get("action", "LEFT_CLICK"))
        action_menu = ctk.CTkOptionMenu(fields, values=ACTION_LIST, variable=action_var)
        action_menu.pack(fill="x")

        ctk.CTkLabel(fields, text="Hand", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))
        hand_var = ctk.StringVar(value=g.get("hand", "any"))
        ctk.CTkOptionMenu(fields, values=["any", "Right", "Left"], variable=hand_var).pack(fill="x")

        ctk.CTkLabel(fields, text="Category", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))
        cat_var = ctk.StringVar(value=g.get("category", "advanced"))
        ctk.CTkOptionMenu(fields, values=list(CATEGORIES.keys()), variable=cat_var).pack(fill="x")

        def save():
            g["name"] = name_e.get()
            g["description"] = desc_e.get()
            g["icon"] = icon_e.get()
            g["action"] = action_var.get()
            g["hand"] = hand_var.get()
            g["category"] = cat_var.get()
            self.config["gestures"][gid] = g
            self.controller.update_gestures(self.config["gestures"])
            save_config(self.config)
            self._refresh_gesture_list()
            win.destroy()

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_row, text="Save", command=save).pack(side="right")
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent",
                      command=win.destroy).pack(side="right", padx=8)

    def _reset_gestures(self):
        if messagebox.askyesno("Reset Gestures",
                                "Reset ALL gestures to default? Custom gestures will be lost."):
            self.config = reset_config()
            self.controller.update_gestures(self.config["gestures"])
            save_config(self.config)
            self._refresh_gesture_list()

    # ─── SETTINGS PAGE ───────────────────────────────────────────────────────────

    def _build_page_settings(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["settings"] = page

        ctk.CTkLabel(page, text="Settings",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(page, corner_radius=12)
        scroll.pack(fill="both", expand=True)

        def section(title):
            ctk.CTkLabel(scroll, text=title,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(
                             anchor="w", padx=12, pady=(16, 4))
            ctk.CTkFrame(scroll, height=1, fg_color="gray40").pack(fill="x", padx=12, pady=(0, 8))

        def slider_row(label, key, from_=1, to=10, is_float=False):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label, width=220, anchor="w").pack(side="left")
            val = self.config["settings"].get(key, (from_ + to) // 2)
            var = ctk.DoubleVar(value=val)
            val_lbl = ctk.CTkLabel(row, text=f"{val:.2f}" if is_float else str(int(val)), width=50)
            def on_change(v, k=key, vl=val_lbl, fl=is_float):
                v2 = round(float(v), 3) if fl else int(float(v))
                self.config["settings"][k] = v2
                vl.configure(text=f"{v2:.3f}" if fl else str(v2))
                self.controller.update_settings(self.config["settings"])
                save_config(self.config)
            slider = ctk.CTkSlider(row, from_=from_, to=to, variable=var, command=on_change)
            slider.pack(side="left", fill="x", expand=True, padx=8)
            val_lbl.pack(side="left")

        def toggle_row(label, key):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label, anchor="w").pack(side="left", fill="x", expand=True)
            var = ctk.BooleanVar(value=self.config["settings"].get(key, True))
            def on_change(k=key, v=var):
                self.config["settings"][k] = v.get()
                self.controller.update_settings(self.config["settings"])
                save_config(self.config)
            ctk.CTkSwitch(row, variable=var, text="", command=on_change).pack(side="right")

        section("📷 Camera")
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="Camera Index (0 = default)", width=220, anchor="w").pack(side="left")
        cam_var = ctk.StringVar(value=str(self.config["settings"].get("camera_index", 0)))
        ctk.CTkOptionMenu(row, values=["0","1","2","3"], variable=cam_var,
                           command=lambda v: self._update_setting("camera_index", int(v))).pack(side="left")
        toggle_row("Mirror Camera (flip horizontally)", "mirror_camera")
        toggle_row("Show hand skeleton on preview", "show_landmarks")
        toggle_row("Show FPS counter", "show_fps")

        section("🖱️ Cursor")
        slider_row("Cursor Smoothing (1=raw, 10=smooth)", "cursor_smoothing", 1, 10)
        slider_row("Cursor Sensitivity", "cursor_sensitivity", 1, 10)
        slider_row("Click Threshold (pinch distance)", "click_threshold", 0.01, 0.12, is_float=True)
        slider_row("Pinch Hold for Drag (×100ms)", "pinch_hold_ms", 100, 800)

        section("📜 Scroll & Zoom")
        slider_row("Scroll Speed", "scroll_speed", 1, 10)
        slider_row("Zoom Speed", "zoom_speed", 1, 10)

        section("🤚 Hand Detection")
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="Dominant Hand", width=220, anchor="w").pack(side="left")
        hand_var = ctk.StringVar(value=self.config["settings"].get("dominant_hand","right"))
        ctk.CTkOptionMenu(row, values=["right","left","auto"], variable=hand_var,
                           command=lambda v: self._update_setting("dominant_hand", v)).pack(side="left")
        toggle_row("Enable Both Hands Simultaneously", "enable_both_hands")
        slider_row("Detection Confidence", "min_detection_confidence", 0.5, 1.0, is_float=True)
        slider_row("Tracking Confidence", "min_tracking_confidence", 0.5, 1.0, is_float=True)

        section("🎨 Appearance")
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="Theme", width=220, anchor="w").pack(side="left")
        theme_var = ctk.StringVar(value=self.config["settings"].get("theme","dark"))
        def set_theme(v):
            ctk.set_appearance_mode(v)
            self._update_setting("theme", v)
        ctk.CTkOptionMenu(row, values=["dark","light","system"], variable=theme_var,
                           command=set_theme).pack(side="left")

        # Reset button
        ctk.CTkButton(scroll, text="Reset All Settings to Default",
                      fg_color="#5a1a1a", hover_color="#7a2a2a",
                      command=self._reset_settings).pack(pady=20)

    def _update_setting(self, key, value):
        self.config["settings"][key] = value
        self.controller.update_settings(self.config["settings"])
        save_config(self.config)

    def _reset_settings(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            from core.config import DEFAULT_SETTINGS
            self.config["settings"] = DEFAULT_SETTINGS.copy()
            save_config(self.config)
            self._build_page_settings()

    # ─── HELP PAGE ───────────────────────────────────────────────────────────────

    def _build_page_help(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["help"] = page

        ctk.CTkLabel(page, text="Help & Gesture Reference",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(page, corner_radius=12)
        scroll.pack(fill="both", expand=True)

        sections = [
            ("🚀 Getting Started", [
                "1. Click ▶ Start in the sidebar — camera will activate.",
                "2. Show your hand to the camera — skeleton should appear.",
                "3. Click ⏸ Pause to freeze gesture actions (preview still runs).",
                "4. Use the Gestures tab to enable/disable or remap any gesture.",
                "5. Use the Settings tab to tune sensitivity and smoothing.",
            ]),
            ("🖱️ Cursor Movement", [
                "• Point your index finger at the camera.",
                "• The fingertip position maps to your screen like a touchpad.",
                "• Adjust Sensitivity and Smoothing in Settings for best results.",
                "• Tip: Use your whole arm slightly — small wrist movements for precision.",
            ]),
            ("👆 Clicking", [
                "• LEFT CLICK: Touch index fingertip to thumb tip (pinch).",
                "• RIGHT CLICK: Touch middle fingertip to thumb tip.",
                "• DOUBLE CLICK: Do two quick left-click pinches in under 0.35s.",
                "• MIDDLE CLICK: Touch ring finger to thumb.",
                "• DRAG: Pinch index+thumb and HOLD for 300ms, then move hand.",
            ]),
            ("📜 Scrolling", [
                "• Raise index + middle finger (others curled).",
                "• Move hand UP to scroll up, DOWN to scroll down.",
                "• Move hand LEFT/RIGHT to scroll horizontally.",
                "• Speed is proportional to how fast you move.",
            ]),
            ("🔍 Zoom", [
                "• Close all fingers except index + thumb (pinch position).",
                "• SPREAD index and thumb apart = ZOOM IN.",
                "• BRING them together = ZOOM OUT.",
                "• Works in browsers, photos, maps, documents.",
            ]),
            ("🪟 Window & Desktop", [
                "• OPEN PALM swipe LEFT = Switch to left virtual desktop (Ctrl+Win+Left).",
                "• OPEN PALM swipe RIGHT = Switch to right virtual desktop.",
                "• OPEN PALM swipe UP = Task View (Win+Tab).",
                "• OPEN PALM swipe DOWN = Show Desktop (Win+D).",
                "• THREE fingers up (tap) = Action Center (Win+A).",
                "• FOUR fingers up (tap) = Alt+Tab (switch apps).",
                "• FIVE fingers SPREAD fast = Close active window (Alt+F4).",
            ]),
            ("🎵 Media Control", [
                "• THUMBS UP (thumb extended, others curled) = Volume Up.",
                "• THUMBS DOWN = Volume Down.",
                "• OK SIGN (index+thumb circle, 3 others extended) = Play/Pause.",
                "• TWO-finger quick swipe RIGHT = Next track.",
                "• TWO-finger quick swipe LEFT = Previous track.",
            ]),
            ("🌐 Browser & Apps", [
                "• L-SHAPE (index + thumb only) = New Tab (Ctrl+T).",
                "• TWO FINGERS CROSSED (very close together) = Close Tab (Ctrl+W).",
                "• SHAKE HAND (oscillate left-right) = Undo (Ctrl+Z).",
                "• SNAP gesture (middle+thumb flick) = Screenshot (Win+Shift+S).",
            ]),
            ("💡 Tips & Tricks", [
                "• Good lighting = much better tracking accuracy.",
                "• Keep hand 30-60cm from camera for best results.",
                "• Plain background helps the camera distinguish your hand.",
                "• If cursor jumps, increase Smoothing in Settings.",
                "• Right hand = thumb on LEFT side. Left hand = thumb on RIGHT side.",
                "  The software detects both automatically based on thumb position.",
                "• You can assign any action to any gesture in the Gestures tab.",
                "• Custom gestures can be added with the + Add Custom button.",
            ]),
        ]

        for title, lines in sections:
            ctk.CTkLabel(scroll, text=title,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(
                             anchor="w", padx=16, pady=(16, 4))
            for line in lines:
                ctk.CTkLabel(scroll, text=line, font=ctk.CTkFont(size=12),
                             text_color="gray", anchor="w", justify="left",
                             wraplength=700).pack(anchor="w", padx=24, pady=1)

    # ─── CONTROLLER ACTIONS ──────────────────────────────────────────────────────

    def _toggle_controller(self):
        if self.controller.is_running:
            self.controller.stop()
            self.toggle_btn.configure(text="▶  Start", fg_color="#1a7a3a", hover_color="#145f2d")
            self.active_btn.configure(state="disabled")
            self.status_label.configure(text="● Stopped", text_color="gray")
        else:
            # Show loading state immediately so user knows it's working
            self.toggle_btn.configure(text="⏳  Starting...", fg_color="#555", state="disabled")
            self.status_label.configure(text="⏳ Opening camera...", text_color="#facc15")
            self.root.update_idletasks()

            def _start_in_thread():
                try:
                    self.controller.start()
                    self.controller.activate()
                    # Update UI back on main thread
                    self.root.after(0, self._on_start_success)
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self._on_start_error(err))

            threading.Thread(target=_start_in_thread, daemon=True).start()

    def _on_start_success(self):
        self.toggle_btn.configure(text="⏹  Stop", fg_color="#7a1a1a",
                                   hover_color="#9a2a2a", state="normal")
        self.active_btn.configure(state="normal", text="⏸  Pause Gestures")
        self.status_label.configure(text="● Active", text_color="#4ade80")

    def _on_start_error(self, err_msg):
        self.toggle_btn.configure(text="▶  Start", fg_color="#1a7a3a",
                                   hover_color="#145f2d", state="normal")
        self.status_label.configure(text="● Error", text_color="#f87171")
        messagebox.showerror("Camera Error", err_msg)

    def _toggle_active(self):
        self.controller.toggle()
        if self.controller.is_active:
            self.active_btn.configure(text="⏸  Pause Gestures")
        else:
            self.active_btn.configure(text="▶  Resume Gestures")

    # ─── CALLBACKS ───────────────────────────────────────────────────────────────

    def _on_frame(self, frame, hands_data):
        try:
            with self._frame_lock:
                self._last_frame = frame.copy()
        except Exception:
            pass

    def _on_action(self, action):
        self._last_action = action
        self._action_time = time.time()

    def _on_status(self, msg):
        self._status_text = msg

    # ─── UI UPDATE LOOP ──────────────────────────────────────────────────────────

    def _start_ui_update(self):
        self._update_ui()

    def _update_ui(self):
        try:
            self._update_camera_preview()
            self._update_status_bar()
            self._update_action_display()
            self._update_hand_info()
        except Exception:
            pass
        self.root.after(33, self._update_ui)  # ~30fps UI refresh

    def _update_camera_preview(self):
        if not PIL_OK:
            return
        try:
            with self._frame_lock:
                frame = self._last_frame.copy() if self._last_frame is not None else None
        except Exception:
            return

        if frame is None:
            return

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to fit label
            label_w = self.cam_label.winfo_width()
            label_h = self.cam_label.winfo_height()
            if label_w < 10 or label_h < 10:
                label_w, label_h = 480, 320

            fh, fw = rgb.shape[:2]
            scale = min(label_w / fw, label_h / fh)
            new_w, new_h = int(fw * scale), int(fh * scale)
            rgb = cv2.resize(rgb, (new_w, new_h))

            img = Image.fromarray(rgb)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
            self.cam_label.configure(image=ctk_img, text="")
            self.cam_label._image = ctk_img  # prevent GC
        except Exception:
            pass

    def _update_status_bar(self):
        if self.controller.is_running:
            if self.controller.is_active:
                self.status_label.configure(text="● Active", text_color="#4ade80")
            else:
                self.status_label.configure(text="⏸ Paused", text_color="#facc15")
            if self.config["settings"].get("show_fps", True):
                self.fps_label.configure(text=f"FPS: {self.controller.fps}")
        else:
            self.status_label.configure(text="● Stopped", text_color="gray")
            self.fps_label.configure(text="FPS: —")

    def _update_action_display(self):
        age = time.time() - self._action_time
        if self._last_action and age < 1.5:
            alpha = max(0, 1.0 - age / 1.5)
            self.action_label.configure(text=self._last_action)
        elif age >= 1.5:
            self.action_label.configure(text="—")

    def _update_hand_info(self):
        hands_data, _ = self.controller._tracker.get_latest() if self.controller._tracker else ([], None)
        if hands_data is None:
            hands_data = []
        if not hands_data:
            self.hand_info_label.configure(text="No hands detected")
        else:
            lines = []
            for h in hands_data:
                ext = h["extended"]
                fingers = " ".join(
                    k[0].upper() for k, v in ext.items() if v
                ) or "none"
                lines.append(
                    f"{h['label']} hand  ·  Fingers up: {fingers}\n"
                    f"  Pinch: {h['pinch_index']:.2f}  Confidence: {h['score']:.0%}"
                )
            self.hand_info_label.configure(text="\n\n".join(lines))

    def _on_close(self):
        self.controller.stop()
        save_config(self.config)
        self.root.destroy()
