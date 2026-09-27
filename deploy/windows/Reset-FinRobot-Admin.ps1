param(
    [string]$ProjectRoot = "C:\Pythology\FinRobot",
    [string]$Email = ""
)

$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }

Push-Location $ProjectRoot
try {
    Write-Host "Inspecting FinRobot authentication database..."
    & $python -c "from finrobot_equity.web_app.database.connection import DATABASE_PATH,DATABASE_URL,SessionLocal; from finrobot_equity.web_app.database import crud; db=SessionLocal(); print('Database:', DATABASE_PATH or DATABASE_URL); users=crud.get_all_users(db); [print(f'USER: {u.email} | provider={u.provider}') for u in users]; db.close()"
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect FinRobot database." }

    if ([string]::IsNullOrWhiteSpace($Email)) {
        $Email = Read-Host "Email to reset (copy one of the USER values above)"
    }

    $secure = Read-Host "New FinRobot password" -AsSecureString
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
from finrobot_equity.web_app.database.connection import SessionLocal, DATABASE_PATH, DATABASE_URL
from finrobot_equity.web_app.database import crud

email = os.environ["FINROBOT_RESET_EMAIL"]
password = os.environ["FINROBOT_RESET_PASSWORD"]
db = SessionLocal()
try:
    user = crud.get_user_by_email(db, email)
    if not user:
        raise SystemExit(f"User not found: {email}")
    crud.update_user_password(db, user, password)
    verified = crud.verify_password(password, user.password_hash)
    print(f"Database: {DATABASE_PATH or DATABASE_URL}")
    print(f"Password updated for: {user.email}")
    print(f"Verification: {'PASS' if verified else 'FAIL'}")
    if not verified:
        raise SystemExit(2)
finally:
    db.close()
"@

    & $python -c $code
    if ($LASTEXITCODE -ne 0) { throw "Password reset/verification failed." }
} finally {
    Pop-Location
    Remove-Item Env:FINROBOT_RESET_EMAIL -ErrorAction SilentlyContinue
    Remove-Item Env:FINROBOT_RESET_PASSWORD -ErrorAction SilentlyContinue
}
