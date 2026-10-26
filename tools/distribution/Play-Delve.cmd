@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Play-Delve.ps1" %*
if errorlevel 1 pause
