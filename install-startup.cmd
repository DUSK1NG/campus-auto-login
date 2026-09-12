@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage-startup.ps1" -Action Install
pause
