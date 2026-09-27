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

function Test-PortListening([int]$Port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

$webLog = Join-Path $logs "finrobot-web.log"
$mt5Log = Join-Path $logs "finrobot-mt5.log"

if (-not (Test-PortListening 8001)) {
    Start-Process -FilePath $venvPython `
        -ArgumentList "run_web_app.py --no-reload" `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $webLog `
        -RedirectStandardError "$webLog.err"
} else {
    Write-Host "FinRobot web already listening on 8001."
}

Start-Sleep -Seconds 3

if (-not (Test-PortListening 8011)) {
    Start-Process -FilePath $venvPython `
        -ArgumentList "run_pythology_mt5.py" `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $mt5Log `
        -RedirectStandardError "$mt5Log.err"
} else {
    Write-Host "Pythology MT5 bridge already listening on 8011."
}

Write-Host "FinRobot web target: http://127.0.0.1:8001"
Write-Host "Pythology MT5 bridge target: http://127.0.0.1:8011"
