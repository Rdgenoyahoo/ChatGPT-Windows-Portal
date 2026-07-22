# Copy this file to portal.env.ps1 to override the defaults.
# Setup-Portal.ps1 does that automatically.

$env:PORTAL_HOME = Split-Path -Parent $PSScriptRoot
$env:PORTAL_BIND_HOST = "127.0.0.1"
$env:PORTAL_PORT = "8000"
$env:PORTAL_SCREENSHOT_DIR = Join-Path $env:PORTAL_HOME "screenshots"
$env:PORTAL_JOB_DIR = Join-Path $env:PORTAL_HOME "jobs"
$env:PORTAL_TESSERACT_PATH = "C:\Program Files\Tesseract-OCR\tesseract.exe"

# Leave blank when using OpenAI Secure MCP Tunnel.
# Set only the hostname (not https:// and not /mcp) for an intentionally
# configured HTTPS reverse proxy.
$env:PORTAL_PUBLIC_HOSTNAME = ""

