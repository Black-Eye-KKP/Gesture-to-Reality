@echo off
title GestureControl - Camera Diagnostic
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
cd /d "%~dp0"
echo Running camera diagnostic as Administrator...
echo.
python camera_test.py
