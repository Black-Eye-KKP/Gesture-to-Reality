@echo off
title GestureControl - Camera Permission Fix
color 0A

echo.
echo  =====================================================
echo   GestureControl - Camera Permission Fix
echo   This will register Python with Windows camera
echo  =====================================================
echo.

:: Self-elevate to Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  Requesting Administrator access...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo  [Running as Administrator] Good.
echo.

:: Find Python executable
set PYTHON_EXE=
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    if not defined PYTHON_EXE set PYTHON_EXE=%%i
)

if not defined PYTHON_EXE (
    :: Try common install locations
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    if exist "C:\Python311\python.exe" set PYTHON_EXE=C:\Python311\python.exe
    if exist "C:\Python312\python.exe" set PYTHON_EXE=C:\Python312\python.exe
    if exist "C:\Python310\python.exe" set PYTHON_EXE=C:\Python310\python.exe
)

if not defined PYTHON_EXE (
    echo  [ERROR] Python not found. Make sure Python is installed.
    pause
    exit /b 1
)

echo  [1/5] Found Python: %PYTHON_EXE%

:: Step 1: Enable camera for ALL desktop apps in registry
echo  [2/5] Enabling camera for desktop apps in registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged" /v "Value" /t REG_SZ /d "Allow" /f >nul 2>&1
echo  Done.

:: Step 2: Register Python specifically as allowed for camera
echo  [3/5] Registering Python for camera access...
:: Convert path: replace \ with #  and : with #
powershell -Command ^
  "$py = '%PYTHON_EXE%' -replace '\\\\', '#' -replace ':', '#'; " ^
  "$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged\' + $py; " ^
  "if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }; " ^
  "Set-ItemProperty -Path $key -Name 'Value' -Value 'Allow' -Force; " ^
  "Set-ItemProperty -Path $key -Name 'LastUsedTimeStart' -Value 0 -Force"
echo  Done.

:: Step 3: Add Python to Windows Firewall
echo  [4/5] Adding Python to Windows Firewall...
netsh advfirewall firewall delete rule name="Python Camera Access" >nul 2>&1
netsh advfirewall firewall add rule name="Python Camera Access" dir=in action=allow program="%PYTHON_EXE%" enable=yes >nul 2>&1
netsh advfirewall firewall add rule name="Python Camera Access" dir=out action=allow program="%PYTHON_EXE%" enable=yes >nul 2>&1
echo  Done.

:: Step 4: Restart Windows Camera Frame Server service
echo  [5/5] Restarting camera service...
net stop FrameServer >nul 2>&1
timeout /t 2 /nobreak >nul
net start FrameServer >nul 2>&1
echo  Done.

echo.
echo  =====================================================
echo   SUCCESS! Camera access granted to Python.
echo  =====================================================
echo.
echo  Now do this:
echo    1. Close GestureControl completely
echo    2. Right-click run.bat
echo    3. Select "Run as administrator"
echo    4. Click Start
echo.
echo  Python found at: %PYTHON_EXE%
echo.
pause
