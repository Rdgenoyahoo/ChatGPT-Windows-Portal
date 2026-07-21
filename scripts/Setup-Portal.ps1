[CmdletBinding()]
param(
    [switch]$SkipTesseract,
    [switch]$NoDesktopShortcut
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

function Test-PythonLauncher {
    param([string]$Executable, [string[]]$PrefixArguments)

    try {
        $version = & $Executable @PrefixArguments -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -ne 0) { return $false }
        $parts = $version.Trim().Split('.')
        return ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 11)
    }
    catch {
        return $false
    }
}

function Find-PythonLauncher {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        if (Test-PythonLauncher "py.exe" @("-3.12")) {
            return @{ Executable = "py.exe"; Arguments = @("-3.12") }
        }
    }

    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        if (Test-PythonLauncher "python.exe" @()) {
            return @{ Executable = "python.exe"; Arguments = @() }
        }
    }

    $knownPath = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path $knownPath) {
        return @{ Executable = $knownPath; Arguments = @() }
    }

    return $null
}

Write-Host ""
Write-Host "ChatGPT Windows Portal installer" -ForegroundColor Cyan
Write-Host "Install folder: $Root"
Write-Host ""

$launcher = Find-PythonLauncher
if ($null -eq $launcher) {
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw "Python 3.11+ was not found and winget is unavailable. Install Python 3.12 from python.org, then run this installer again."
    }

    Write-Host "Installing Python 3.12 for the current user..." -ForegroundColor Yellow
    & winget.exe install --exact --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget could not install Python 3.12." }

    $launcher = Find-PythonLauncher
    if ($null -eq $launcher) {
        throw "Python was installed but could not be located. Close this window and run Install-Portal.bat again."
    }
}

Write-Host "Creating the isolated Python environment..." -ForegroundColor Yellow
if (-not (Test-Path $VenvPython)) {
    & $launcher.Executable @($launcher.Arguments) -m venv (Join-Path $Root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
}

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }

& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install Portal dependencies." }

$ConfigFile = Join-Path $Root "config\portal.env.ps1"
if (-not (Test-Path $ConfigFile)) {
    Copy-Item (Join-Path $Root "config\portal.env.example.ps1") $ConfigFile
}

if (-not $SkipTesseract) {
    $Tesseract = "C:\Program Files\Tesseract-OCR\tesseract.exe"
    if (-not (Test-Path $Tesseract)) {
        if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
            Write-Host "Installing optional Tesseract OCR support..." -ForegroundColor Yellow
            & winget.exe install --exact --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Tesseract was not installed. The Portal still works, but OCR tools will be unavailable."
            }
        }
        else {
            Write-Warning "winget is unavailable, so optional Tesseract OCR was skipped."
        }
    }
}

Write-Host "Running the self-check..." -ForegroundColor Yellow
& $VenvPython (Join-Path $Root "scripts\self_check.py")
if ($LASTEXITCODE -ne 0) { throw "Portal self-check failed." }

if (-not $NoDesktopShortcut) {
    try {
        $Desktop = [Environment]::GetFolderPath("Desktop")
        $ShortcutPath = Join-Path $Desktop "ChatGPT Windows Portal.lnk"
        $Shell = New-Object -ComObject WScript.Shell
        $Shortcut = $Shell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = Join-Path $Root "Start-Portal.bat"
        $Shortcut.WorkingDirectory = $Root
        $Shortcut.Description = "Start ChatGPT Windows Portal"
        $Shortcut.Save()
        Write-Host "Desktop shortcut created: $ShortcutPath"
    }
    catch {
        Write-Warning "The Portal installed, but the desktop shortcut could not be created: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "Portal installation completed." -ForegroundColor Green
Write-Host "1. Run Start-Portal.bat to test the local server."
Write-Host "2. Run Configure-Secure-Tunnel.bat to connect it privately to ChatGPT."

