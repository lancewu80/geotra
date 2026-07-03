@echo off
REM Double-click this to start everything (Postgres + backend + frontend).
REM Same thing as running:
REM   powershell -ExecutionPolicy Bypass -File start.ps1
REM Safe to run every time you want to (re)start the system, including
REM after a reboot.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause
