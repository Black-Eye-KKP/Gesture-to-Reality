# ✋ GestureControl — Hand Gesture Mouse for Windows 11

Control your entire Windows PC with hand gestures through your webcam.
No special hardware needed — just your laptop's built-in camera.

---

## 📋 Requirements

- Windows 10 or Windows 11
- Python 3.10, 3.11, or 3.12
- Webcam (built-in laptop camera works perfectly)
- 4GB RAM minimum

---

## 🚀 Installation (Step by Step)

### Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.11** (recommended) or 3.10 / 3.12
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box **"Add Python to PATH"** before clicking Install
5. Click "Install Now"

### Step 2 — Download GestureControl

If you have a ZIP file:
1. Right-click the ZIP → **Extract All**
2. Choose a permanent location (e.g. `C:\GestureControl\`)

### Step 3 — Run the Installer

1. Open the extracted folder
2. Double-click **`install.bat`**
3. Wait 2–5 minutes while packages download
4. You should see: `[OK] All core packages verified`

### Step 4 — Launch the App

- Double-click **`run.bat`** (also saved to Desktop during install)
- OR open Command Prompt in the folder and type: `python main.py`

---

## 🎮 How to Use

### Starting

1. Launch the app → you'll see the **Dashboard**
2. Click **▶ Start** in the left sidebar
3. Allow camera access if Windows asks
4. Your camera preview appears — position your hand in front of the camera
5. The hand skeleton (dots + lines) should appear on your hand
6. Gestures are now controlling your mouse!

### Pausing

- Click **⏸ Pause Gestures** to freeze gesture actions (useful when typing)
- Camera preview still runs — just actions are paused
- Click **▶ Resume** to reactivate

---

## 🤌 Full Gesture List

### 🖱️ Cursor Control
| Gesture | Action |
|---------|--------|
| ☝️ Point index finger | Move cursor (like touchpad) |

### 👆 Clicking
| Gesture | Action |
|---------|--------|
| Pinch index + thumb | Left Click |
| Pinch middle + thumb | Right Click |
| Two quick pinches (index+thumb) | Double Click |
| Pinch ring + thumb | Middle Click |
| Pinch + hold 300ms + move | Click & Drag |

### 📜 Scrolling
| Gesture | Action |
|---------|--------|
| ✌️ Index+middle fingers up, swipe UP | Scroll Up |
| ✌️ Index+middle fingers up, swipe DOWN | Scroll Down |
| ✌️ Index+middle fingers up, swipe LEFT | Scroll Left / Browser Back |
| ✌️ Index+middle fingers up, swipe RIGHT | Scroll Right / Browser Forward |

### 🔍 Zoom
| Gesture | Action |
|---------|--------|
| Pinch pose + SPREAD index+thumb apart | Zoom In (Ctrl++) |
| Pinch pose + BRING index+thumb together | Zoom Out (Ctrl+-) |

### 🪟 Window Management
| Gesture | Action |
|---------|--------|
| 🖐️ Open palm swipe LEFT | Virtual Desktop Left (Ctrl+Win+←) |
| 🖐️ Open palm swipe RIGHT | Virtual Desktop Right (Ctrl+Win+→) |
| 🖐️ Open palm swipe UP | Task View (Win+Tab) |
| 🖐️ Open palm swipe DOWN | Show Desktop (Win+D) |
| 🤟 Three fingers up, tap | Action Center (Win+A) |
| 🖐️ Four fingers up, tap | Alt+Tab (switch apps) |
| ✋ Five fingers spread + fast open | Close Window (Alt+F4) |
| ✊ Fist | Grab selection |

### 🎵 Media Control
| Gesture | Action |
|---------|--------|
| 👍 Thumbs Up | Volume Up |
| 👎 Thumbs Down | Volume Down |
| 👌 OK sign (index+thumb circle) | Play / Pause |
| ✌️ Two-finger quick swipe RIGHT | Next Track |
| ✌️ Two-finger quick swipe LEFT | Previous Track |

### 🌐 Browser & Apps
| Gesture | Action |
|---------|--------|
| L-shape (index + thumb only) | New Tab (Ctrl+T) |
| ✌️ Two fingers very close / crossed | Close Tab (Ctrl+W) |
| Shake hand left-right | Undo (Ctrl+Z) |
| Snap fingers (middle+thumb flick) | Screenshot (Win+Shift+S) |

### 🤖 Advanced
| Gesture | Action |
|---------|--------|
| Draw circle in air with index | Rotate selected object |
| Tilt wrist counter-clockwise | Rotate Left |
| Tilt wrist clockwise | Rotate Right |

---

## ⚙️ Customization

### Remap Any Gesture
1. Go to **Gestures** tab
2. Find the gesture you want to change
3. Click **Edit**
4. Choose a new action from the dropdown
5. Click **Save**

### Add Your Own Gestures
1. Go to **Gestures** tab
2. Click **+ Add Custom**
3. Name your gesture and pick an action
4. Save — the gesture is registered (you'll still need to implement detection logic in `core/gesture_engine.py`)

### Adjust Performance
Go to **Settings** tab:
- **Cursor Smoothing**: Higher = smoother but slightly more lag
- **Cursor Sensitivity**: Higher = cursor moves more with less hand movement
- **Click Threshold**: Lower = needs closer pinch to click
- **Scroll Speed**: How fast scrolling feels

---

## 💡 Tips for Best Results

1. **Lighting matters** — face a window or use a desk lamp. Avoid backlighting.
2. **Distance** — keep hand 30–60cm (1–2 feet) from camera
3. **Plain background** — a plain wall behind your hand helps detection
4. **Camera angle** — camera pointing straight at you works best
5. **Right hand** — thumb on LEFT side of hand from camera's view
6. **Left hand** — thumb on RIGHT side from camera's view
7. If cursor jumps: increase Smoothing to 8–9
8. If gestures aren't detected: lower Detection Confidence to 0.6

---

## 🗂️ File Structure

```
GestureControl/
├── main.py                  ← Entry point — run this
├── run.bat                  ← Windows launcher (double-click)
├── install.bat              ← One-click installer
├── requirements.txt         ← Python packages
├── gesture_config.json      ← Your saved settings (auto-created)
├── core/
│   ├── config.py            ← Settings & gesture definitions
│   ├── tracker.py           ← MediaPipe hand tracking
│   ├── gesture_engine.py    ← Gesture recognition logic
│   ├── action_executor.py   ← Windows mouse/keyboard control
│   └── controller.py        ← Main coordinator
└── ui/
    └── app.py               ← GUI (customtkinter)
```

---

## 🛠️ Troubleshooting

**"Python not found" during install.bat**
→ Reinstall Python and make sure to check "Add Python to PATH"

**Camera not starting**
→ Close other apps using the camera (Teams, Zoom, Camera app)
→ Try changing Camera Index to 1 or 2 in Settings

**Hand skeleton not showing**
→ Improve lighting
→ Lower Detection Confidence in Settings

**Cursor moving erratically**
→ Increase Smoothing slider (try 8–9)
→ Keep hand more still while moving slowly

**Gestures not firing**
→ Check the Gestures tab — make sure the gesture is toggled ON
→ Increase the gesture hold time slightly

**"Module not found" error**
→ Run `install.bat` again, or manually: `pip install -r requirements.txt`

---

Run files accordingly:
- FIX_CAMERA_PERMISSION.bat
- install.bat
- INSTALL_OLLAMA.bat
- INSTALL_PYTHON311.bat
- RUN_DIAGNOSTIC.bat
- SETUP_AI.bat
- run.bat(It's the last file you should run. Before that you may face error)

## 📄 License

MIT License — free for personal and commercial use.
