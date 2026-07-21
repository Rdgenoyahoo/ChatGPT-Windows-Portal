[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$TunnelExe = & (Join-Path $PSScriptRoot "Install-Secure-Tunnel.ps1") | Select-Object -Last 1

Write-Host ""
Write-Host "OpenAI Secure MCP Tunnel configuration" -ForegroundColor Cyan
Write-Host "You need a tunnel ID and a runtime API key."
Write-Host "Create them in these official pages:"
Write-Host "  Tunnel: https://platform.openai.com/settings/organization/tunnels"
Write-Host "  Runtime key: https://platform.openai.com/settings/organization/api-keys"
Write-Host ""
Write-Host "The runtime API key is never written to disk by this project." -ForegroundColor Green
Write-Host ""

$TunnelId = (Read-Host "Paste your tunnel ID (tunnel_ plus 32 lowercase hex characters)").Trim()
if ($TunnelId -notmatch '^tunnel_[0-9a-f]{32}$') {
    throw "That tunnel ID is not in the expected format."
}

$PortalConfig = Join-Path $Root "config\portal.env.ps1"
$Port = "8000"
if (Test-Path $PortalConfig) {
    . $PortalConfig
    if ($env:PORTAL_PORT) { $Port = $env:PORTAL_PORT }
}

$McpUrl = "http://127.0.0.1:$Port/mcp"
$TunnelConfig = Join-Path $Root "config\secure-tunnel.env.ps1"
$configText = @"
# Machine-specific tunnel settings. Runtime API keys do not belong in this file.
`$env:CONTROL_PLANE_TUNNEL_ID = "$TunnelId"
`$env:MCP_SERVER_URL = "$McpUrl"
"@
Set-Content -Path $TunnelConfig -Value $configText -Encoding UTF8

Write-Host "Saved the non-secret tunnel ID and local MCP address." -ForegroundColor Green
Write-Host "Checking the tunnel-client binary..."
& $TunnelExe --version
if ($LASTEXITCODE -ne 0) { throw "tunnel-client could not start." }

Write-Host ""
Write-Host "Configuration completed." -ForegroundColor Green
Write-Host "Run Start-Portal-and-Tunnel.bat and enter your runtime API key when prompted."

