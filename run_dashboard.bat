@echo off
title NeuBench-Automator Dashboard
echo ========================================================
echo   Launching NeuBench-Automator Dashboard...
echo   Platforms: X, LinkedIn, Bluesky
echo ========================================================

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [Setup] Virtual environment not found. Running initial setup first...
    call setup.bat
)

echo Starting web server on http://127.0.0.1:8000
.\venv\Scripts\python.exe -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000
pause
