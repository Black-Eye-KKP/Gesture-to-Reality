@echo off
title GestureControl - AI Setup (Ollama)
color 0B

echo.
echo  =====================================================
echo   GestureControl - Local AI Setup
echo   This installs Ollama (free, local, no internet AI)
echo   It runs on your CPU - no GPU needed
echo  =====================================================
echo.

echo  [1/3] Downloading Ollama installer...
echo  (This is ~100MB - wait for browser to download)
echo.
start https://ollama.com/download/OllamaSetup.exe
echo.
echo  After Ollama installs:
echo  1. Come back here and press any key
echo  2. We will download the llama3.2 model (~2GB)
echo.
pause

echo.
echo  [2/3] Pulling llama3.2 model (small, fast, CPU-friendly)...
echo  This is a one-time download of ~2GB. Wait for it to finish.
echo.
ollama pull llama3.2

echo.
echo  [3/3] Testing Ollama connection...
ollama run llama3.2 "Say: AI ready" --nowordwrap

echo.
echo  =====================================================
echo   AI Setup Complete!
echo   GestureControl will now learn from your usage.
echo  =====================================================
echo.
echo  How it works:
echo    - Every gesture is logged to gesture_log.jsonl
echo    - The AI analyzes patterns and adjusts thresholds
echo    - Click accuracy improves the more you use it
echo    - No data leaves your laptop - fully local
echo.
pause
