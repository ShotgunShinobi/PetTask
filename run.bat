@echo off
title Desktop Pet Taskbar Companion
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [DesktopPet] Setting up isolated Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

echo [DesktopPet] Starting your taskbar pet...
start "" ".venv\Scripts\pythonw.exe" main.py
exit
