[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run Install-Portal.bat first." }

Write-Host "Checking Python source..."
& $Python -m py_compile (Join-Path $Root "portal\server.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Checking Portal metadata and tool registration..."
& $Python (Join-Path $Root "scripts\self_check.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Checking PowerShell syntax..."
Get-ChildItem (Join-Path $Root "scripts") -Filter "*.ps1" | ForEach-Object {
    $null = [scriptblock]::Create((Get-Content $_.FullName -Raw))
}

Write-Host "All checks passed." -ForegroundColor Green

