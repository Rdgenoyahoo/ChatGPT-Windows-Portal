# Troubleshooting

## `Portal is not installed`

Run `Install-Portal.bat`. Confirm this file then exists:

```text
.venv\Scripts\python.exe
```

## Python installation fails

Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/windows/), enable the Python launcher during setup, then rerun `Install-Portal.bat`.

## PowerShell blocks a script

The `.bat` launchers use `-ExecutionPolicy Bypass` only for their own scripts. You can also right-click the downloaded ZIP, open **Properties**, select **Unblock**, and extract it again.

## Port 8000 is already in use

Edit `config\portal.env.ps1` and choose another unused port:

```powershell
$env:PORTAL_PORT = "8010"
```

Then rerun `Configure-Secure-Tunnel.bat` so its saved MCP URL matches.

To inspect the port:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

## OCR tools report Tesseract missing

Install it with:

```powershell
winget install --exact --id UB-Mannheim.TesseractOCR
```

If it is installed elsewhere, set `PORTAL_TESSERACT_PATH` in `config\portal.env.ps1`.

## Screenshots work but clicking by text does not

Text clicking depends on Tesseract and screen scaling. First test `ocr_screen`, then use `find_text_on_screen`. Windows UI Automation through `list_ui_elements` and `click_ui_element` is usually more reliable than OCR.

## Secure tunnel download fails

The downloader requires GitHub access and validates the release against `SHA256SUMS.txt`. Download the current Windows archive manually from the official [`openai/tunnel-client` releases](https://github.com/openai/tunnel-client/releases/latest), verify the published checksum, and place `tunnel-client.exe` at:

```text
tools\tunnel-client.exe
```

## `doctor` reports authentication or permission errors

- Make sure you entered a runtime API key, not an admin API key.
- Confirm the runtime key's principal has **Tunnels Read + Use**.
- Confirm the tunnel ID belongs to the selected Platform organization.
- Create a fresh runtime key if the old key was revoked.
- Do not paste the key into an issue, log, screenshot, or configuration file.

## Tunnel is healthy but ChatGPT cannot see it

The tunnel must be associated with the target ChatGPT workspace as well as the Platform organization. Recheck the association in [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels), then verify Developer mode and tunnel permissions.

## A Portal tool is missing after an update

Restart both terminals, then open **Settings → Plugins → Windows Portal → Refresh** in ChatGPT.

## Run the complete local check

```powershell
.\scripts\Test-Portal.ps1
```

When reporting a bug, include the self-check output and Python version, but remove usernames, paths, tunnel IDs, API keys, screenshots, and document contents.

