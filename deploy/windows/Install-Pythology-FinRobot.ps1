param(
    [string]$ProjectRoot = "C:\Pythology\FinRobot",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
Write-Host "Installing Pythology FinRobot experiment into $ProjectRoot"

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root does not exist. Clone PythologyIntelligence/FinRobot to $ProjectRoot first."
}

Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    & $PythonExe -m venv .venv
}

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$pip = Join-Path $ProjectRoot ".venv\Scripts\pip.exe"

& $venvPython -m pip install --upgrade pip
& $pip install -r requirements-equity.txt
& $pip install -r requirements-pythology-mt5.txt

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "runtime\logs") | Out-Null

$taskName = "Pythology FinRobot"
$startScript = Join-Path $ProjectRoot "deploy\windows\Start-Pythology-FinRobot.ps1"
$action = New-ScheduledTaskAction `
    -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -ProjectRoot `"$ProjectRoot`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $taskSettings `
    -Force | Out-Null

Write-Host "Installed scheduled task: $taskName"
Write-Host "Execution defaults to SHADOW. Real-money execution is not implemented."
Write-Host "Start now with: Start-ScheduledTask -TaskName `"$taskName`""
