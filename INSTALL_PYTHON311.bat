@echo off
title Install Python 3.11 for GestureControl
color 0A

echo.
echo  ============================================
echo   Installing Python 3.11 for GestureControl
echo   (MediaPipe does NOT support Python 3.14)
echo  ============================================
echo.

:: Self-elevate
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo  [Step 1] Checking if Python 3.11 already installed...
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo  Python 3.11 already installed!
    py -3.11 --version
    goto :setup_packages
)

echo  [Step 2] Installing Python 3.11 via winget...
echo  (Windows will show a progress bar - wait for it to finish)
echo.
winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements

if %errorlevel% neq 0 (
    echo.
    echo  winget install failed. Trying direct download method...
    echo.
    echo  Please manually:
    echo    1. Open this URL in your browser:
    echo       https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo    2. Run the installer
    echo    3. CHECK "Add Python 3.11 to PATH"
    echo    4. Click Install Now
    echo    5. Come back and run this file again
    echo.
    pause
    exit /b 1
)

echo.
echo  [Step 3] Verifying Python 3.11...
:: Refresh PATH
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
set "PATH=C:\Python311;C:\Python311\Scripts;%PATH%"

py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python 3.11 installed but not found by launcher yet.
    echo  Close this window and reopen run.bat - it should work now.
    pause
    exit /b
)

:setup_packages
echo.
echo  [Step 4] Installing MediaPipe and all packages for Python 3.11...
py -3.11 -m pip install --upgrade pip --quiet
py -3.11 -m pip install mediapipe==0.10.14 opencv-python pyautogui pynput customtkinter Pillow numpy screeninfo

if %errorlevel% neq 0 (
    echo  [ERROR] Package install failed.
    pause & exit /b 1
)

echo.
echo  [Step 5] Verifying packages...
py -3.11 -c "import mediapipe as mp; print('  mediapipe', mp.__version__, '- OK')"
py -3.11 -c "import cv2; print('  opencv', cv2.__version__, '- OK')"
py -3.11 -c "import customtkinter; print('  customtkinter - OK')"

echo.
echo  [Step 6] Updating run.bat to use Python 3.11...
cd /d "%~dp0"
echo @echo off > run.bat
echo title GestureControl >> run.bat
echo net session ^>nul 2^>^&1 >> run.bat
echo if %%errorlevel%% neq 0 ( >> run.bat
echo     powershell -Command "Start-Process '%%~f0' -Verb RunAs" >> run.bat
echo     exit /b >> run.bat
echo ) >> run.bat
echo cd /d "%%~dp0" >> run.bat
echo echo Starting GestureControl with Python 3.11... >> run.bat
echo py -3.11 main.py >> run.bat
echo if %%errorlevel%% neq 0 ( >> run.bat
echo     echo [ERROR] Failed to start. >> run.bat
echo     pause >> run.bat
echo ) >> run.bat

echo.
echo  ============================================
echo   DONE! Python 3.11 + MediaPipe installed.
echo  ============================================
echo.
echo  Now:
echo    1. Close this window
echo    2. Right-click run.bat -> Run as administrator
echo    3. Click Start in the app
echo.
pause
