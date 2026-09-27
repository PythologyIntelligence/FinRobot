param(
    [string]$CaddyRoot = "C:\Pythology\caddy",
    [string]$Hostname = "finrobot.pythology.co.nz",
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$caddy = Join-Path $CaddyRoot "caddy.exe"
$config = Join-Path $CaddyRoot "Caddyfile"

if (-not (Test-Path $caddy)) { throw "Caddy executable not found: $caddy" }
if (-not (Test-Path $config)) { throw "Caddyfile not found: $config" }

$raw = Get-Content $config -Raw
if ($raw -notmatch [regex]::Escape($Hostname)) {
    $block = @"

$Hostname {
    reverse_proxy 127.0.0.1:$Port
}
"@
    Add-Content -Path $config -Value $block
    Write-Host "Added $Hostname -> 127.0.0.1:$Port to Caddyfile."
} else {
    Write-Host "$Hostname already exists in Caddyfile; leaving existing block unchanged."
}

& $caddy validate --config $config --adapter caddyfile
if ($LASTEXITCODE -ne 0) { throw "Caddy validation failed. Configuration was not reloaded." }

& $caddy reload --config $config --adapter caddyfile
if ($LASTEXITCODE -ne 0) { throw "Caddy reload failed." }

Write-Host "Caddy reloaded successfully."
Write-Host "Public target: https://$Hostname"
Write-Host "Remember: DNS for $Hostname must resolve to this VPS public IP."
