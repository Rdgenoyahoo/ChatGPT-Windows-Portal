[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$ToolsDir = Join-Path $Root "tools"
$TunnelExe = Join-Path $ToolsDir "tunnel-client.exe"

if (Test-Path $TunnelExe) {
    Write-Output $TunnelExe
    return
}

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "Downloading the latest official OpenAI tunnel-client release..." -ForegroundColor Yellow

$headers = @{ "User-Agent" = "ChatGPT-Windows-Portal-installer" }
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/openai/tunnel-client/releases/latest" -Headers $headers
$architecture = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
$assetPattern = "tunnel-client-*-windows-$architecture.zip"
$asset = $release.assets | Where-Object { $_.name -like $assetPattern } | Select-Object -First 1
$sumsAsset = $release.assets | Where-Object { $_.name -eq "SHA256SUMS.txt" } | Select-Object -First 1

if ($null -eq $asset -or $null -eq $sumsAsset) {
    throw "The latest official release does not contain the expected Windows package or checksum file."
}

$TempDir = Join-Path ([IO.Path]::GetTempPath()) ("chatgpt-windows-portal-" + [Guid]::NewGuid().ToString("N"))
$ZipPath = Join-Path $TempDir $asset.name
$SumsPath = Join-Path $TempDir "SHA256SUMS.txt"
$ExpandPath = Join-Path $TempDir "expanded"

New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
    Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $ZipPath
    Invoke-WebRequest -UseBasicParsing -Uri $sumsAsset.browser_download_url -OutFile $SumsPath

    $hashLine = Get-Content $SumsPath | Where-Object { $_ -match ([regex]::Escape($asset.name) + '$') } | Select-Object -First 1
    if (-not $hashLine) { throw "No checksum was published for $($asset.name)." }

    $expectedHash = ($hashLine -split '\s+')[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "The tunnel-client checksum did not match the official release. Nothing was installed."
    }

    Expand-Archive -Path $ZipPath -DestinationPath $ExpandPath -Force
    $downloadedExe = Get-ChildItem $ExpandPath -Recurse -Filter "tunnel-client.exe" | Select-Object -First 1
    if ($null -eq $downloadedExe) { throw "tunnel-client.exe was not found in the official package." }

    New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null
    Copy-Item $downloadedExe.FullName $TunnelExe -Force
}
finally {
    if (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
}

Write-Host "Installed and checksum-verified: $TunnelExe" -ForegroundColor Green
Write-Output $TunnelExe

