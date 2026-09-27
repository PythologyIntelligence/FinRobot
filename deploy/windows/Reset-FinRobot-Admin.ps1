param(
    [string]$ProjectRoot = "C:\Pythology\FinRobot",
    [string]$Email = "admin@finrobot.com"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }

$secure = Read-Host "New FinRobot admin password" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}

$env:FINROBOT_RESET_EMAIL = $Email
$env:FINROBOT_RESET_PASSWORD = $plain

$code = @"
import os
from finrobot_equity.web_app.database.connection import SessionLocal
from finrobot_equity.web_app.database import crud

email = os.environ["FINROBOT_RESET_EMAIL"]
password = os.environ["FINROBOT_RESET_PASSWORD"]
db = SessionLocal()
try:
    user = crud.get_user_by_email(db, email)
    if not user:
        raise SystemExit(f"Admin user not found: {email}")
    crud.update_user_password(db, user, password)
    print(f"Password updated for {email}")
finally:
    db.close()
"@

Push-Location $ProjectRoot
try {
    & $python -c $code
} finally {
    Pop-Location
    Remove-Item Env:FINROBOT_RESET_EMAIL -ErrorAction SilentlyContinue
    Remove-Item Env:FINROBOT_RESET_PASSWORD -ErrorAction SilentlyContinue
}
