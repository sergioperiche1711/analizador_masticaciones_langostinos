@echo off
cd /d "%~dp0"
echo Preparando el analizador. Se necesita conexion a Internet.
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python 3.10 o posterior mediante el comando py.
    echo Instala Python desde https://www.python.org/downloads/windows/
    echo Durante la instalacion activa la opcion de agregar Python al PATH.
    pause
    exit /b 1
)
if not exist "%~dp0.venv\Scripts\python.exe" (
    py -3 -m venv "%~dp0.venv"
    if errorlevel 1 goto error
)
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto error
echo.
echo Instalacion completada. Abre "Abrir analizador.bat".
pause
exit /b 0
:error
echo.
echo La instalacion no se completo. Revisa el mensaje anterior y la conexion a Internet.
pause
exit /b 1
