@echo off
title NeuBench X-Post-Automater Setup
echo ========================================================
echo   NeuBench X-Post-Automater 1-Click Environment Setup
echo ========================================================

cd /d "%~dp0"

echo [1/3] Creating Python Virtual Environment...
if not exist "venv" (
    python -m venv venv
)

echo [2/3] Installing Dependencies...
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip.exe install -r requirements.txt

echo [3/3] Installing Headless Chromium for Automation...
.\venv\Scripts\playwright.exe install chromium

echo ========================================================
echo   Setup Complete!
echo   To log into your X account, run:
echo   .\venv\Scripts\python.exe main.py login
echo ========================================================
pause

