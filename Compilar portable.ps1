$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot 'python-completo\python\python.exe'
& $pythonExe -m PyInstaller --noconfirm --windowed --onedir --noupx --name ZounD --collect-all soundfile --collect-all _soundfile_data desktop.py
if ($LASTEXITCODE -ne 0) { throw 'Error de compilación' }
Copy-Item -LiteralPath 'PORTABLE.md' -Destination 'dist\ZounD\LEEME.md'
Write-Host 'Compilación creada en dist\ZounD. No está firmada digitalmente.'
