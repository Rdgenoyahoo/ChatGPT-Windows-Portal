[CmdletBinding()]
param([switch]$DoctorOnly)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$ConfigFile = Join-Path $Root "config\secure-tunnel.env.ps1"
$TunnelExe = Join-Path $Root "tools\tunnel-client.exe"

if (-not (Test-Path $ConfigFile)) {
    throw "Secure Tunnel is not configured. Run Configure-Secure-Tunnel.bat first."
}
if (-not (Test-Path $TunnelExe)) {
    throw "tunnel-client is not installed. Run Configure-Secure-Tunnel.bat first."
}

. $ConfigFile

$keyWasProvided = -not [string]::IsNullOrWhiteSpace($env:CONTROL_PLANE_API_KEY)
$keyPointer = [IntPtr]::Zero
try {
    if (-not $keyWasProvided) {
        $secureKey = Read-Host "Paste the OpenAI runtime API key (input is hidden)" -AsSecureString
        $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    }

    Write-Host "Running Secure MCP Tunnel diagnostics..." -ForegroundColor Yellow
    & $TunnelExe doctor --explain
    if ($LASTEXITCODE -ne 0) { throw "tunnel-client diagnostics failed. See the messages above." }

    if (-not $DoctorOnly) {
        Write-Host ""
        Write-Host "Starting OpenAI Secure MCP Tunnel." -ForegroundColor Cyan
        Write-Host "Local status UI: http://127.0.0.1:8080/ui"
        Write-Host "Keep this window open. Press Ctrl+C to stop the tunnel."
        & $TunnelExe run --log.level=info --log.format=struct-text
        exit $LASTEXITCODE
    }
}
finally {
    if (-not $keyWasProvided) {
        Remove-Item Env:\CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
    }
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
}

