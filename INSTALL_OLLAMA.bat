@echo off
title Install Ollama - Local AI for GestureControl
color 0B

echo.
echo  ============================================
echo   Installing Ollama - Free Local AI
echo   No GPU needed - runs on your Ryzen 7 CPU
echo  ============================================
echo.

:: Check if already installed
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo  Ollama already installed!
    ollama --version
    goto :pull_model
)

echo  [1/3] Downloading Ollama installer...
echo  This downloads ~100MB. Please wait.
echo.
powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe' -UseBasicParsing"

echo  [2/3] Installing Ollama...
"%TEMP%\OllamaSetup.exe" /S
timeout /t 5 /nobreak >nul

:pull_model
echo  [3/3] Downloading phi3 AI model (2.3GB, one-time download)...
echo  This is the AI brain that learns your gestures.
echo  Runs entirely on your CPU - no internet needed after this.
echo.
start /wait ollama pull phi3

echo.
echo  ============================================
echo   Ollama + phi3 AI installed!
echo  ============================================
echo.
echo  The AI will now:
echo   - Detect ghost inputs automatically
echo   - Learn your pinch style and adjust thresholds
echo   - Improve precision over time
echo.
echo  To enable: open GestureControl Settings -> AI Learning -> ON
echo.
pause
