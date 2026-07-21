[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$ConfigFile = Join-Path $Root "config\portal.env.ps1"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Portal is not installed. Run Install-Portal.bat first."
}

if (Test-Path $ConfigFile) {
    . $ConfigFile
}
else {
    $env:PORTAL_HOME = $Root
    $env:PORTAL_BIND_HOST = "127.0.0.1"
    $env:PORTAL_PORT = "8000"
}

Set-Location $Root
Write-Host "Starting ChatGPT Windows Portal at http://127.0.0.1:$($env:PORTAL_PORT)/mcp" -ForegroundColor Cyan
Write-Host "Keep this window open. Press Ctrl+C to stop the Portal."
Write-Host ""

& $VenvPython (Join-Path $Root "portal\server.py")
exit $LASTEXITCODE

