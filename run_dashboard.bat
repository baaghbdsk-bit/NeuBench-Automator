@echo off
title NeuBench-Automator Omnichannel Dashboard
echo ========================================================
echo   Launching NeuBench-Automator Dashboard...
echo   Omnichannel OS for 𝕏, Bluesky, LinkedIn & Threads
echo ========================================================

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [Setup] Virtual environment not found. Running initial setup first...
    call setup.bat
)

echo Starting web server on http://127.0.0.1:8000
.\venv\Scripts\python.exe main.py dashboard
pause

