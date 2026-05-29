@echo off
title GestureControl

:: Self-elevate to Administrator (camera access requires it)
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
echo  Starting GestureControl...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GestureControl failed to start.
    echo Make sure you ran install.bat first.
    pause
)
