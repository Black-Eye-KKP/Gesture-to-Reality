@echo off
title GestureControl — Installer
color 0A

echo.
echo  ============================================
echo    GestureControl — Hand Gesture Mouse
echo    Windows 11 Installer
echo  ============================================
echo.

:: Check Python version - mediapipe requires 3.8-3.11
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found!
    echo  Install Python 3.11 from: https://www.python.org/downloads/release/python-3119/
    echo  CHECK "Add Python to PATH" during install!
    pause & exit /b 1
)

:: Get Python version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python version detected: %PYVER%

:: Extract major.minor
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJ=%%a
    set PYMIN=%%b
)

echo  Major: %PYMAJ%  Minor: %PYMIN%

if %PYMAJ% NEQ 3 (
    echo  [ERROR] Python 3 required. You have Python %PYVER%
    goto :wrong_version
)

:: mediapipe supports 3.8 to 3.11 only
if %PYMIN% GTR 11 (
    goto :wrong_version
)
if %PYMIN% LSS 8 (
    goto :wrong_version
)

echo  [OK] Python %PYVER% is compatible with MediaPipe.
goto :install

:wrong_version
echo.
echo  ============================================
echo   WRONG PYTHON VERSION: %PYVER%
echo  ============================================
echo.
echo  MediaPipe (hand tracking) ONLY supports Python 3.8 to 3.11.
echo  Your Python %PYVER% is NOT supported.
echo.
echo  YOU MUST install Python 3.11 separately:
echo.
echo    1. Go to: https://www.python.org/downloads/release/python-3119/
echo    2. Download "Windows installer (64-bit)"
echo    3. Install it - CHECK "Add to PATH"
echo    4. After install, open a NEW Command Prompt
echo    5. Type: py -3.11 --version
echo    6. If it shows 3.11.x, run this installer again
echo.
echo  NOTE: Keep your existing Python %PYVER% - just ADD Python 3.11 alongside it.
echo  Windows can have multiple Python versions installed at once.
echo.
pause
exit /b 1

:install
echo.
echo  [1/4] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo  [2/4] Installing dependencies...
echo        mediapipe, opencv, pyautogui, customtkinter, pynput, Pillow...
python -m pip install mediapipe==0.10.14 opencv-python pyautogui pynput customtkinter Pillow numpy screeninfo

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Install failed. Try running as Administrator.
    pause & exit /b 1
)

echo  [3/4] Verifying...
python -c "import mediapipe; print('  mediapipe:', mediapipe.__version__)"
python -c "import cv2; print('  opencv:', cv2.__version__)"
python -c "import customtkinter; print('  customtkinter: OK')"

echo  [4/4] Creating desktop shortcut...
set SCRIPT_DIR=%~dp0
echo @echo off > "%USERPROFILE%\Desktop\GestureControl.bat"
echo cd /d "%SCRIPT_DIR%" >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo net session ^>nul 2^>^&1 >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo if %%errorlevel%% neq 0 ( >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo     powershell -Command "Start-Process '%%~f0' -Verb RunAs" >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo     exit /b >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo ) >> "%USERPROFILE%\Desktop\GestureControl.bat"
echo python main.py >> "%USERPROFILE%\Desktop\GestureControl.bat"

echo.
echo  ============================================
echo    Installation Complete!
echo  ============================================
echo.
echo  Run: Right-click run.bat -> Run as administrator
echo.
pause
