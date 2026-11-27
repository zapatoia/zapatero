# Instalador automático de la skill · Windows 10/11. Sin administrador.
# Se puede correr las veces que haga falta: sigue donde se quedó.
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File "<carpeta de la skill>\instalar\instalar.ps1"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$uvVer = '0.11.32'
$herr = Join-Path $env:USERPROFILE '.club-videos\bin'
New-Item -ItemType Directory -Force -Path $herr | Out-Null
$uv = Join-Path $herr 'uv.exe'
$arm = ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') -or ($env:PROCESSOR_ARCHITEW6432 -eq 'ARM64')

if (-not (Test-Path $uv)) {
  $arq = if ($arm) { 'aarch64' } else { 'x86_64' }
  Write-Host 'Bajando uv (instala Python sin administrador)...'
  $zip = Join-Path $env:TEMP 'uv-club.zip'
  $tmp = Join-Path $env:TEMP 'uv-club'
  Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/download/$uvVer/uv-$arq-pc-windows-msvc.zip" -OutFile $zip
  if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
  Expand-Archive -Path $zip -DestinationPath $tmp -Force
  $exe = Get-ChildItem -Path $tmp -Recurse -Filter 'uv.exe' | Select-Object -First 1
  Copy-Item $exe.FullName $uv -Force
  Remove-Item -Recurse -Force $tmp
  Remove-Item -Force $zip
}

$kit = Get-Content -Raw -Encoding UTF8 (Join-Path $aqui 'kit.json') | ConvertFrom-Json
$pyv = if ($kit.python) { [string]$kit.python } else { '3.12' }
# PC con procesador ARM (Snapdragon): Python x64, porque OpenCV no tiene versión ARM64 para Windows.
if ($arm) { $pyv = "cpython-$pyv-windows-x86_64-none" }

$env:UV_EXE = $uv
$env:PY_REQ = $pyv
$env:UV_PYTHON_PREFERENCE = 'only-managed'
$env:PYTHONUTF8 = '1'
& $uv run --quiet --no-project --python $pyv (Join-Path $aqui 'instalar.py') @args
exit $LASTEXITCODE
