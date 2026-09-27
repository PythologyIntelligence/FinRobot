param(
    [string]$ProjectRoot = "C:\Pythology\FinRobot"
)

$ErrorActionPreference = "Stop"
$runtime = Join-Path $ProjectRoot "runtime"
$logs = Join-Path $runtime "logs"
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $logs | Out-Null

if (-not (Test-Path $venvPython)) {
    throw "FinRobot venv Python not found: $venvPython"
}

$webLog = Join-Path $logs "finrobot-web.log"
$mt5Log = Join-Path $logs "finrobot-mt5.log"

Start-Process -FilePath $venvPython `
    -ArgumentList "run_web_app.py" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $webLog `
    -RedirectStandardError "$webLog.err"

Start-Sleep -Seconds 3

Start-Process -FilePath $venvPython `
    -ArgumentList "run_pythology_mt5.py" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $mt5Log `
    -RedirectStandardError "$mt5Log.err"

Write-Host "FinRobot web requested on its configured port."
Write-Host "Pythology MT5 bridge requested on http://127.0.0.1:8011"
