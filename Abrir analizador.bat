@echo off
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0app.py"
) else if exist "%~dp0python-completo\python\python.exe" (
    "%~dp0python-completo\python\python.exe" "%~dp0app.py"
) else (
    echo No se encontro Python para el analizador.
    echo Primero instala Python y ejecuta "Instalar dependencias.bat".
    echo Consulta README.md para ver los pasos.
    pause
    exit /b 1
)
if errorlevel 1 (
    echo.
    echo No se pudo abrir el analizador. Revisa el mensaje anterior.
    pause
    exit /b 1
)
