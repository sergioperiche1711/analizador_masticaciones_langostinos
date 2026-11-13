@echo off
cd /d "%~dp0"
if exist "..\python-completo\python\python.exe" (
  start "" http://localhost:8000
  "..\python-completo\python\python.exe" -m http.server 8000 --bind 127.0.0.1
) else (
  py -3 --version >nul 2>&1
  if errorlevel 1 (
    echo No se encontro Python. Consulta LEEME.md para abrir la vista previa.
    pause
    exit /b 1
  )
  start "" http://localhost:8000
  py -3 -m http.server 8000 --bind 127.0.0.1
)
echo La vista previa se ha detenido. Revisa cualquier mensaje anterior.
pause
