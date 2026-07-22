# ChatGPT Windows Portal

A Windows MCP server that gives ChatGPT permission-controlled tools for troubleshooting software, working with files, running diagnostics, and operating the visible desktop.

The installer builds an isolated Python environment, installs the Portal's dependencies, adds optional OCR support, and creates a desktop shortcut. The recommended connection uses [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), so the MCP server stays on `127.0.0.1` and is not exposed directly to the public internet.

> [!CAUTION]
> This is a powerful remote-control tool. It can run commands, write files, launch applications, and control the mouse and keyboard. Use it only on a computer you own or administer. Start with ChatGPT's **Always ask** permission level and never publish API keys, tunnel configuration, or screenshots.

## What it includes

- 63 MCP tools for system diagnostics, files, processes, Python, networking, screenshots, OCR, Windows UI Automation, mouse/keyboard control, and application launching.
- Persistent concurrent background jobs with per-job process tracking, timeouts, status, and separate output logs.
- Local-only defaults: `127.0.0.1:8000/mcp` with DNS-rebinding protection.
- A double-click Windows installer and desktop shortcut.
- A checksum-verified downloader for the official OpenAI `tunnel-client` Windows release.
- Secure key handling: the runtime API key is entered into a hidden prompt and is not saved by this project.
- Self-checks and Windows CI validation.
- No model files, cloud API usage, subscription, or GPU is required by the Portal itself.

## Requirements

- Windows 10 or Windows 11.
- Internet access during installation.
- `winget` for fully automatic Python and optional Tesseract installation. If `winget` is unavailable, install Python 3.11 or newer manually first.
- A ChatGPT account with Developer mode available.
- For the recommended private connection: an OpenAI Platform organization with Secure MCP Tunnel access, a tunnel ID, and a runtime API key with **Tunnels Read + Use**.

## Quick start

### 1. Download

Open this repository's green **Code** button, choose **Download ZIP**, and extract it to a permanent folder such as:

```text
C:\ChatGPT-Windows-Portal
```

You can also clone it with Git:

```powershell
git clone https://github.com/Rdgenoyahoo/ChatGPT-Windows-Portal.git
cd ChatGPT-Windows-Portal
```

### 2. Install

Double-click:

```text
Install-Portal.bat
```

The installer:

1. Finds Python 3.11+ or installs Python 3.12 with `winget`.
2. Creates `.venv` inside the project folder.
3. Installs the pinned Python dependencies.
4. Installs Tesseract OCR when possible.
5. runs the self-check.
6. creates a **ChatGPT Windows Portal** desktop shortcut.

To skip OCR from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Setup-Portal.ps1 -SkipTesseract
```

### 3. Test the local Portal

Double-click `Start-Portal.bat`. A terminal should show:

```text
Local MCP URL: http://127.0.0.1:8000/mcp
```

Keep that window open. In another PowerShell window, run:

```powershell
.\scripts\Test-Portal.ps1
```

### 4. Configure OpenAI Secure MCP Tunnel

1. Open [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels) and create a tunnel associated with the ChatGPT workspace that will use it.
2. Create a runtime API key in [organization API keys](https://platform.openai.com/settings/organization/api-keys). The key's principal needs **Tunnels Read + Use**.
3. Double-click `Configure-Secure-Tunnel.bat` and paste the tunnel ID when requested.

That script downloads the latest official Windows `tunnel-client` from [`openai/tunnel-client`](https://github.com/openai/tunnel-client/releases/latest), verifies it against the release's SHA-256 checksum, and stores only the non-secret tunnel ID and local MCP address. It does **not** save the runtime API key.

### 5. Start the Portal and tunnel

Double-click:

```text
Start-Portal-and-Tunnel.bat
```

Two terminals are used:

- the Portal server at `127.0.0.1:8000`;
- the Secure MCP Tunnel client, which asks for the runtime API key with hidden input.

Keep both terminals open. Tunnel health is available locally at `http://127.0.0.1:8080/ui`.

### 6. Add it to ChatGPT

1. In ChatGPT, open **Settings → Security and login** and enable **Developer mode**.
2. Open **Settings → Plugins**, or go to [chatgpt.com/plugins](https://chatgpt.com/plugins).
3. Select the plus button to create a developer-mode app.
4. Name it `Windows Portal` and describe it as a private MCP for Windows diagnostics, files, and desktop control.
5. Under **Connection**, choose **Tunnel**, then select your tunnel or paste its tunnel ID.
6. After ChatGPT displays the tool list, create the app.
7. Set its permission level to **Always ask** while testing.

See [the detailed ChatGPT connection guide](docs/CHATGPT_SETUP.md) for testing prompts, refreshing tools, and account/workspace troubleshooting.

## Example prompts

Start with read-only requests:

- `Use Windows Portal to show system and disk status.`
- `List the top-level files in C:\AI without changing anything.`
- `Show which Python executable and packages this program is using.`
- `Capture the desktop and tell me which application windows are open.`
- `Run two read-only diagnostics as background jobs and show each status and output separately.`

Then approve changes deliberately:

- `Create a backup and update this configuration file.`
- `Launch the application from this exact path.`
- `Bring the named window forward and click its Save button.`

Mutating tools use explicit confirmation strings such as WRITE_FILE, RUN_MUTATING_COMMAND, START_MUTATING_JOB, STOP_JOB, CONTROL_DESKTOP, and LAUNCH_PROGRAM. These are safety interlocks for normal use; transport security and ChatGPT permissions remain essential.

## Tool groups

| Group | Examples | Changes the PC? |
|---|---|---:|
| Status | system, disks, ports, processes, environment | No |
| Files | list, inspect, read, tail, find, search | No |
| File changes | write and append with optional backup | Yes |
| Commands | PowerShell, cmd, Python, pip | Sometimes |
| Background jobs | start, list, monitor, read output, stop, and delete records | Sometimes |
| Desktop vision | screenshot, window capture, OCR, image/text search | No |
| Desktop control | mouse, keyboard, UI Automation, window management | Yes |
| Programs | launch executable or Start-menu app | Yes |

The complete categorized list is in [docs/TOOLS.md](docs/TOOLS.md).

## Configuration

Setup copies `config/portal.env.example.ps1` to the ignored file `config/portal.env.ps1`.

| Variable | Default | Purpose |
|---|---|---|
| `PORTAL_HOME` | repository folder | Default command working directory |
| `PORTAL_BIND_HOST` | `127.0.0.1` | MCP listener address |
| `PORTAL_PORT` | `8000` | MCP listener port |
| `PORTAL_SCREENSHOT_DIR` | `screenshots` | Saved screenshots |
| `PORTAL_JOB_DIR` | `jobs` | Persistent job metadata and output logs |
| `PORTAL_TESSERACT_PATH` | standard Program Files path | OCR executable |
| `PORTAL_PUBLIC_HOSTNAME` | blank | Optional hostname for an intentionally secured reverse proxy |

Keep `PORTAL_BIND_HOST=127.0.0.1` with Secure MCP Tunnel. Do not set it to `0.0.0.0` unless you understand and control the network boundary.

## Updating

If installed with Git:

```powershell
git pull
.\Install-Portal.bat
```

The installer reuses the virtual environment, updates the dependencies to the pinned versions, preserves local configuration, and reruns the self-check.

If installed from a ZIP, extract the new version to a fresh folder, then copy only your ignored `config\portal.env.ps1` and `config\secure-tunnel.env.ps1` files if you want to retain those settings.

## Troubleshooting and security

- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security model and safe operation](SECURITY.md)
- [Detailed ChatGPT setup](docs/CHATGPT_SETUP.md)
- [Tool catalog](docs/TOOLS.md)

## Project status

This is an independent community project, not an official OpenAI product. OpenAI, ChatGPT, MCP, Windows, and Tesseract are trademarks or projects of their respective owners.

## License

[MIT](LICENSE)

