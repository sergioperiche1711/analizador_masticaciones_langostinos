@echo off
cd /d "%~dp0"
"%~dp0python-completo\python\python.exe" "%~dp0app.py"
if errorlevel 1 pause
