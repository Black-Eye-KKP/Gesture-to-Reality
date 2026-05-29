"""
camera_test.py - Run this FIRST to diagnose exactly what is blocking the camera.
Usage: python camera_test.py
"""
import sys
import os
import time

print("=" * 60)
print("  GestureControl - Camera Diagnostic Tool")
print("=" * 60)
print()

# Step 1: Check registry
print("[1] Checking Windows camera permission registry...")
try:
    import winreg
    paths_to_check = [
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam",
         "HKCU webcam"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam",
         "HKLM webcam"),
    ]
    for hive, path, label in paths_to_check:
        try:
            with winreg.OpenKey(hive, path) as k:
                val, _ = winreg.QueryValueEx(k, "Value")
                print(f"    {label} = {val}")
        except Exception as e:
            print(f"    {label} = ERROR: {e}")

    # Check NonPackaged
    np_path = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, np_path) as k:
            val, _ = winreg.QueryValueEx(k, "Value")
            print(f"    NonPackaged = {val}")
            # List subkeys (registered desktop apps)
            print(f"    Registered desktop apps:")
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(k, i)
                    print(f"      - {subkey[:80]}")
                    i += 1
                except OSError:
                    break
    except Exception as e:
        print(f"    NonPackaged = ERROR: {e}")
except ImportError:
    print("    winreg not available (not Windows?)")

print()

# Step 2: Check if running as admin
print("[2] Checking admin status...")
try:
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    print(f"    Running as Administrator: {'YES' % () if is_admin else 'NO - this may be the problem'}")
except:
    print("    Could not check admin status")

print()

# Step 3: Try every camera backend
print("[3] Trying all camera backends...")
try:
    import cv2
    backends = [
        (cv2.CAP_MSMF,  "CAP_MSMF  (Microsoft Media Foundation - Windows 11)"),
        (cv2.CAP_DSHOW, "CAP_DSHOW (DirectShow - legacy Windows)"),
        (0,             "CAP_ANY   (Auto-detect)"),
    ]
    found = False
    for idx in range(4):
        for backend_id, backend_name in backends:
            try:
                cap = cv2.VideoCapture(idx, backend_id)
                if cap.isOpened():
                    # Try reading
                    ok = False
                    for _ in range(10):
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            ok = True
                            break
                        time.sleep(0.05)
                    status = "✓ WORKS" if ok else "opened but no frames"
                    print(f"    Index {idx} | {backend_name}: {status}")
                    if ok:
                        found = True
                    cap.release()
                else:
                    print(f"    Index {idx} | {backend_name}: failed to open")
            except Exception as e:
                print(f"    Index {idx} | {backend_name}: EXCEPTION: {e}")
    if not found:
        print()
        print("    *** NO CAMERA BACKEND WORKED ***")
        print("    This confirms a system-level block (Samsung security or driver issue)")
except ImportError:
    print("    opencv-python not installed! Run: pip install opencv-python")

print()

# Step 4: Check for Samsung blocking software
print("[4] Checking for Samsung/OEM security software...")
import subprocess
result = subprocess.run(
    ["powershell", "-Command",
     "Get-Process | Where-Object {$_.Name -like '*samsung*' -or $_.Name -like '*secur*' -or $_.Name -like '*privacy*'} | Select-Object Name, Id | Format-Table -AutoSize"],
    capture_output=True, text=True, timeout=10
)
if result.stdout.strip():
    print("    Found running Samsung/security processes:")
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            print(f"    {line}")
else:
    print("    No obvious Samsung security processes found")

print()

# Step 5: Check Windows camera frame server
print("[5] Checking Windows Camera Frame Server service...")
result = subprocess.run(
    ["sc", "query", "FrameServer"],
    capture_output=True, text=True, timeout=5
)
for line in result.stdout.split('\n'):
    if 'STATE' in line or 'NAME' in line:
        print(f"    {line.strip()}")

print()
print("=" * 60)
print("  Diagnostic complete. Share this output for next steps.")
print("=" * 60)
input("\nPress Enter to exit...")
