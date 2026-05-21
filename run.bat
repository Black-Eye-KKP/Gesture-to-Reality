@echo off 
title GestureControl 
net session >nul 2>&1 
if %errorlevel% neq 0 ( 
    powershell -Command "Start-Process '%~f0' -Verb RunAs" 
    exit /b 
) 
cd /d "%~dp0" 
echo Starting GestureControl with Python 3.11... 
py -3.11 main.py 
if %errorlevel% neq 0 ( 
    echo [ERROR] Failed to start. 
    pause 
) 
