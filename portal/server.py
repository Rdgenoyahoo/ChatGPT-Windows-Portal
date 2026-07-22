from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

import os
import sys
import platform
import socket
import subprocess
import shutil
import glob
import time
from pathlib import Path

try:
    import psutil
except Exception:
    psutil = None


# Optional desktop-control modules are installed by Setup-Portal.ps1.
try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import mss
except Exception:
    mss = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

try:
    import pygetwindow as gw
except Exception:
    gw = None

try:
    import pywinauto
    from pywinauto import Desktop, Application
except Exception:
    pywinauto = None
    Desktop = None
    Application = None

try:
    import pytesseract
    _tesseract_exe = os.getenv(
        "PORTAL_TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )
    if os.path.exists(_tesseract_exe):
        pytesseract.pytesseract.tesseract_cmd = _tesseract_exe
except Exception:
    pytesseract = None


PORTAL_HOME = Path(
    os.getenv("PORTAL_HOME", str(Path(__file__).resolve().parents[1]))
).resolve()
HOST = os.getenv("PORTAL_BIND_HOST", "127.0.0.1").strip() or "127.0.0.1"
PORT = int(os.getenv("PORTAL_PORT", "8000"))
HOSTNAME = os.getenv("PORTAL_PUBLIC_HOSTNAME", "").strip()
SCREENSHOT_DIR = Path(
    os.getenv("PORTAL_SCREENSHOT_DIR", str(PORTAL_HOME / "screenshots"))
).resolve()
MAX_RETURN_CHARS = 30000


print("Starting ChatGPT Windows Portal...")


allowed_hosts = [f"127.0.0.1:{PORT}", f"localhost:{PORT}"]
allowed_origins = [f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"]

if HOSTNAME:
    allowed_hosts.append(HOSTNAME)
    allowed_origins.append(f"https://{HOSTNAME}")


mcp = FastMCP(
    "ChatGPT Windows Portal",
    host=HOST,
    port=PORT,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    ),
)


def truncate_text(text, limit=MAX_RETURN_CHARS):
    if text is None:
        return ""

    text = str(text)

    if len(text) <= limit:
        return text

    return text[:limit] + f"\n\n--- TRUNCATED TO {limit} CHARACTERS ---"


def resolve_path(path):
    if not path:
        path = "."

    expanded = os.path.expandvars(os.path.expanduser(path))
    return Path(expanded).resolve()


def run_process(args, cwd=None, timeout_seconds=60):
    try:
        timeout_seconds = max(1, min(int(timeout_seconds), 300))

        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            errors="replace",
        )

        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": truncate_text(result.stdout),
            "stderr": truncate_text(result.stderr),
        }

    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": None,
            "stdout": truncate_text(e.stdout or ""),
            "stderr": truncate_text(e.stderr or ""),
            "error": f"Timed out after {timeout_seconds} seconds.",
        }

    except Exception as e:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": str(e),
        }


def command_is_blocked(command):
    cmd = command.lower()

    blocked = [
        "format ",
        "diskpart",
        "shutdown",
        "restart-computer",
        "bcdedit",
        "cipher /w",
        "remove-item c:\\",
        "remove-item -recurse c:\\",
        "del c:\\",
        "rd c:\\",
        "reg delete hklm",
        "reg delete hkcu",
    ]

    return any(x in cmd for x in blocked)


def command_needs_confirm(command):
    cmd = command.lower()

    risky = [
        "remove-item",
        "del ",
        "erase ",
        "rmdir",
        "rd ",
        "set-content",
        "add-content",
        "new-item",
        "copy-item",
        "move-item",
        "rename-item",
        "pip install",
        "python -m pip install",
        "conda install",
        "winget install",
        "winget uninstall",
        "npm install",
        "git clone",
        "git pull",
        "git reset",
        "invoke-webrequest",
        "curl ",
        "wget ",
        "start-process",
        "stop-process",
        "taskkill",
        "netsh",
        "reg add",
        "reg delete",
    ]

    return any(x in cmd for x in risky)


@mcp.tool()
def hello() -> str:
    """Returns a simple greeting."""
    return "Hello from ChatGPT Windows Portal!"


@mcp.tool()
def portal_status() -> dict:
    """Returns status for the MCP portal and local server."""
    return {
        "ok": True,
        "portal_name": "ChatGPT Windows Portal",
        "bind_host": HOST,
        "hostname": HOSTNAME or None,
        "local_mcp_url": f"http://127.0.0.1:{PORT}/mcp",
        "public_mcp_url": f"https://{HOSTNAME}/mcp" if HOSTNAME else None,
        "portal_home": str(PORTAL_HOME),
        "cwd": os.getcwd(),
        "server_file": str(Path(__file__).resolve()),
        "python_executable": sys.executable,
        "python_version": sys.version,
    }


@mcp.tool()
def system_summary() -> dict:
    """Returns basic system information."""
    info = {
        "ok": True,
        "computer_name": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "current_directory": os.getcwd(),
    }

    if psutil is not None:
        try:
            mem = psutil.virtual_memory()
            info.update(
                {
                    "cpu_physical_cores": psutil.cpu_count(logical=False),
                    "cpu_logical_cores": psutil.cpu_count(logical=True),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "ram_total_gb": round(mem.total / (1024 ** 3), 2),
                    "ram_available_gb": round(mem.available / (1024 ** 3), 2),
                    "ram_used_percent": mem.percent,
                    "boot_time": time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(psutil.boot_time()),
                    ),
                }
            )
        except Exception as e:
            info["psutil_error"] = str(e)
    else:
        info["psutil"] = "not installed"

    return info


@mcp.tool()
def disk_summary() -> dict:
    """Returns disk usage information."""
    if psutil is None:
        return {
            "ok": False,
            "error": "psutil is not installed.",
        }

    disks = []

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)

            disks.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "filesystem": part.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent,
                }
            )

        except Exception as e:
            disks.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "error": str(e),
                }
            )

    return {
        "ok": True,
        "disks": disks,
    }


@mcp.tool()
def current_directory() -> dict:
    """Returns the server working directory."""
    return {
        "ok": True,
        "cwd": os.getcwd(),
        "server_file": str(Path(__file__).resolve()),
    }


@mcp.tool()
def list_directory(path: str = ".", max_items: int = 200) -> dict:
    """Lists files and folders in a directory."""
    try:
        p = resolve_path(path)
        max_items = max(1, min(int(max_items), 1000))

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path does not exist.",
            }

        if not p.is_dir():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path is not a directory.",
            }

        items = []

        for child in list(p.iterdir())[:max_items]:
            try:
                st = child.stat()

                items.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "type": "directory" if child.is_dir() else "file",
                        "size_bytes": st.st_size if child.is_file() else None,
                        "modified": time.strftime(
                            "%Y-%m-%d %H:%M:%S",
                            time.localtime(st.st_mtime),
                        ),
                    }
                )

            except Exception as e:
                items.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "error": str(e),
                    }
                )

        return {
            "ok": True,
            "path": str(p),
            "count": len(items),
            "items": items,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def file_info(path: str) -> dict:
    """Returns information about one file or folder."""
    try:
        p = resolve_path(path)

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path does not exist.",
            }

        st = p.stat()

        return {
            "ok": True,
            "path": str(p),
            "name": p.name,
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "size_bytes": st.st_size,
            "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_ctime)),
            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def read_text_file(path: str, max_chars: int = 30000) -> dict:
    """Reads a text file."""
    try:
        p = resolve_path(path)
        max_chars = max(1, min(int(max_chars), 100000))

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "File does not exist.",
            }

        if not p.is_file():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path is not a file.",
            }

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(max_chars + 1)

        return {
            "ok": True,
            "path": str(p),
            "truncated": len(data) > max_chars,
            "content": data[:max_chars],
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def tail_text_file(path: str, lines: int = 200) -> dict:
    """Returns the last lines of a text file."""
    try:
        p = resolve_path(path)
        lines = max(1, min(int(lines), 2000))

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "File does not exist.",
            }

        if not p.is_file():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path is not a file.",
            }

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        return {
            "ok": True,
            "path": str(p),
            "lines_returned": min(lines, len(all_lines)),
            "content": truncate_text("".join(all_lines[-lines:])),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def write_text_file(
    path: str,
    content: str,
    overwrite: bool = False,
    make_backup: bool = True,
    confirm: str = "",
) -> dict:
    """
    Writes a text file.
    Requires confirm='WRITE_FILE'.
    """
    try:
        if confirm != "WRITE_FILE":
            return {
                "ok": False,
                "error": "Refusing to write. Use confirm='WRITE_FILE'.",
            }

        p = resolve_path(path)

        if p.exists() and not overwrite:
            return {
                "ok": False,
                "path": str(p),
                "error": "File exists. Set overwrite=True.",
            }

        p.parent.mkdir(parents=True, exist_ok=True)

        backup_path = None

        if p.exists() and make_backup:
            backup_path = str(p) + ".bak"
            shutil.copy2(p, backup_path)

        with open(p, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)

        return {
            "ok": True,
            "path": str(p),
            "backup_path": backup_path,
            "bytes_written": len(content.encode("utf-8", errors="replace")),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def append_text_file(path: str, content: str, confirm: str = "") -> dict:
    """
    Appends text to a file.
    Requires confirm='APPEND_FILE'.
    """
    try:
        if confirm != "APPEND_FILE":
            return {
                "ok": False,
                "error": "Refusing to append. Use confirm='APPEND_FILE'.",
            }

        p = resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "a", encoding="utf-8", errors="replace") as f:
            f.write(content)

        return {
            "ok": True,
            "path": str(p),
            "bytes_appended": len(content.encode("utf-8", errors="replace")),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def find_files(root: str, pattern: str = "*", max_results: int = 200) -> dict:
    """Finds files using a glob pattern."""
    try:
        root_path = resolve_path(root)
        max_results = max(1, min(int(max_results), 1000))

        if not root_path.exists():
            return {
                "ok": False,
                "root": str(root_path),
                "error": "Root does not exist.",
            }

        results = []
        search_pattern = str(root_path / "**" / pattern)

        for match in glob.iglob(search_pattern, recursive=True):
            results.append(match)

            if len(results) >= max_results:
                break

        return {
            "ok": True,
            "root": str(root_path),
            "pattern": pattern,
            "count": len(results),
            "results": results,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def search_text_in_files(
    root: str,
    text: str,
    file_pattern: str = "*.py",
    max_files: int = 500,
    max_matches: int = 100,
) -> dict:
    """Searches text inside files."""
    try:
        root_path = resolve_path(root)
        max_files = max(1, min(int(max_files), 5000))
        max_matches = max(1, min(int(max_matches), 1000))

        if not root_path.exists():
            return {
                "ok": False,
                "root": str(root_path),
                "error": "Root does not exist.",
            }

        matches = []
        files_checked = 0
        needle = text.lower()
        search_pattern = str(root_path / "**" / file_pattern)

        for file_name in glob.iglob(search_pattern, recursive=True):
            if files_checked >= max_files or len(matches) >= max_matches:
                break

            p = Path(file_name)

            if not p.is_file():
                continue

            files_checked += 1

            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    for line_number, line in enumerate(f, start=1):
                        if needle in line.lower():
                            matches.append(
                                {
                                    "path": str(p),
                                    "line": line_number,
                                    "text": line.strip(),
                                }
                            )

                            if len(matches) >= max_matches:
                                break

            except Exception:
                pass

        return {
            "ok": True,
            "root": str(root_path),
            "text": text,
            "file_pattern": file_pattern,
            "files_checked": files_checked,
            "matches_returned": len(matches),
            "matches": matches,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def which(program: str) -> dict:
    """Finds an executable on PATH."""
    try:
        found = shutil.which(program)

        return {
            "ok": found is not None,
            "program": program,
            "path": found,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def check_port(host: str = "127.0.0.1", port: int = 8000, timeout_seconds: int = 3) -> dict:
    """Checks whether a TCP host and port are reachable."""
    try:
        port = int(port)
        timeout_seconds = max(1, min(int(timeout_seconds), 30))

        with socket.create_connection((host, port), timeout=timeout_seconds):
            return {
                "ok": True,
                "host": host,
                "port": port,
                "reachable": True,
            }

    except Exception as e:
        return {
            "ok": False,
            "host": host,
            "port": port,
            "reachable": False,
            "error": str(e),
        }


@mcp.tool()
def list_processes(name_filter: str = "", max_results: int = 100) -> dict:
    """Lists running processes."""
    if psutil is None:
        return {
            "ok": False,
            "error": "psutil is not installed.",
        }

    try:
        max_results = max(1, min(int(max_results), 500))
        filt = name_filter.lower().strip()
        processes = []

        for proc in psutil.process_iter(
            ["pid", "name", "exe", "cmdline", "username", "memory_info"]
        ):
            if len(processes) >= max_results:
                break

            try:
                info = proc.info
                name = info.get("name") or ""
                cmdline_raw = info.get("cmdline") or []
                cmdline = (
                    " ".join(cmdline_raw)
                    if isinstance(cmdline_raw, list)
                    else str(cmdline_raw)
                )

                if filt:
                    haystack = f"{name} {cmdline}".lower()

                    if filt not in haystack:
                        continue

                mem = info.get("memory_info")
                rss_mb = round(mem.rss / (1024 ** 2), 2) if mem else None

                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": name,
                        "exe": info.get("exe"),
                        "cmdline": truncate_text(cmdline, 1000),
                        "username": info.get("username"),
                        "rss_mb": rss_mb,
                    }
                )

            except Exception:
                pass

        return {
            "ok": True,
            "name_filter": name_filter,
            "count": len(processes),
            "processes": processes,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def kill_process(pid: int, confirm: str = "") -> dict:
    """
    Kills a process by PID.
    Requires confirm='KILL_PID'.
    """
    if psutil is None:
        return {
            "ok": False,
            "error": "psutil is not installed.",
        }

    try:
        if confirm != "KILL_PID":
            return {
                "ok": False,
                "error": "Refusing to kill process. Use confirm='KILL_PID'.",
            }

        proc = psutil.Process(int(pid))
        name = proc.name()
        proc.kill()

        return {
            "ok": True,
            "pid": int(pid),
            "name": name,
            "message": "Process killed.",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def run_powershell(
    command: str,
    cwd: str = "",
    timeout_seconds: int = 60,
    confirm: str = "",
) -> dict:
    """
    Runs a PowerShell command.
    Risky commands require confirm='RUN_MUTATING_COMMAND'.
    """
    try:
        command = command.strip()

        if not command:
            return {
                "ok": False,
                "error": "No command provided.",
            }

        if command_is_blocked(command):
            return {
                "ok": False,
                "error": "Blocked dangerous command.",
                "command": command,
            }

        if command_needs_confirm(command) and confirm != "RUN_MUTATING_COMMAND":
            return {
                "ok": False,
                "error": "Command may change the system. Use confirm='RUN_MUTATING_COMMAND'.",
                "command": command,
            }

        cwd_path = resolve_path(cwd or str(PORTAL_HOME))

        if not cwd_path.exists():
            return {
                "ok": False,
                "error": "Working directory does not exist.",
                "cwd": str(cwd_path),
            }

        result = run_process(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            cwd=str(cwd_path),
            timeout_seconds=timeout_seconds,
        )

        result["command"] = command
        result["cwd"] = str(cwd_path)

        return result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def run_cmd(
    command: str,
    cwd: str = "",
    timeout_seconds: int = 60,
    confirm: str = "",
) -> dict:
    """
    Runs a cmd.exe command.
    Risky commands require confirm='RUN_MUTATING_COMMAND'.
    """
    try:
        command = command.strip()

        if not command:
            return {
                "ok": False,
                "error": "No command provided.",
            }

        if command_is_blocked(command):
            return {
                "ok": False,
                "error": "Blocked dangerous command.",
                "command": command,
            }

        if command_needs_confirm(command) and confirm != "RUN_MUTATING_COMMAND":
            return {
                "ok": False,
                "error": "Command may change the system. Use confirm='RUN_MUTATING_COMMAND'.",
                "command": command,
            }

        cwd_path = resolve_path(cwd or str(PORTAL_HOME))

        if not cwd_path.exists():
            return {
                "ok": False,
                "error": "Working directory does not exist.",
                "cwd": str(cwd_path),
            }

        result = run_process(
            [
                "cmd.exe",
                "/c",
                command,
            ],
            cwd=str(cwd_path),
            timeout_seconds=timeout_seconds,
        )

        result["command"] = command
        result["cwd"] = str(cwd_path)

        return result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def python_version(python_exe: str = "python") -> dict:
    """Returns Python executable and version."""
    return run_process(
        [
            python_exe,
            "-c",
            "import sys; print(sys.executable); print(sys.version)",
        ],
        timeout_seconds=30,
    )


@mcp.tool()
def python_import_check(
    package_name: str,
    python_exe: str = "",
) -> dict:
    """Checks whether a Python package imports."""
    python_exe = python_exe or sys.executable
    code = (
        "import importlib.util; "
        f"name={package_name!r}; "
        "spec=importlib.util.find_spec(name); "
        "print('FOUND' if spec else 'MISSING'); "
        "print(spec.origin if spec else '')"
    )

    result = run_process(
        [
            python_exe,
            "-c",
            code,
        ],
        timeout_seconds=30,
    )

    result["package_name"] = package_name
    result["python_exe"] = python_exe

    return result


@mcp.tool()
def pip_list(
    python_exe: str = "",
    timeout_seconds: int = 60,
) -> dict:
    """Lists installed pip packages."""
    python_exe = python_exe or sys.executable
    return run_process(
        [
            python_exe,
            "-m",
            "pip",
            "list",
        ],
        timeout_seconds=timeout_seconds,
    )


@mcp.tool()
def environment_variables(name_filter: str = "") -> dict:
    """Returns environment variables, redacting secrets."""
    try:
        filt = name_filter.lower().strip()
        variables = {}

        for key, value in os.environ.items():
            if filt and filt not in key.lower():
                continue

            lower_key = key.lower()

            if (
                "token" in lower_key
                or "secret" in lower_key
                or "password" in lower_key
                or "key" in lower_key
            ):
                variables[key] = "***REDACTED***"
            else:
                variables[key] = value

        return {
            "ok": True,
            "name_filter": name_filter,
            "variables": variables,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def ngrok_status() -> dict:
    """Checks ngrok-related local status."""
    status = {
        "ok": True,
        "expected_hostname": HOSTNAME or None,
        "expected_public_mcp_url": f"https://{HOSTNAME}/mcp" if HOSTNAME else None,
        "ngrok_path": shutil.which("ngrok"),
        "ngrok_web_interface_4040": check_port("127.0.0.1", 4040),
        "local_mcp": check_port("127.0.0.1", PORT),
    }

    if psutil is not None:
        ngrok_processes = []

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info.get("name") or ""
                cmdline_raw = proc.info.get("cmdline") or []
                cmdline = (
                    " ".join(cmdline_raw)
                    if isinstance(cmdline_raw, list)
                    else str(cmdline_raw)
                )

                if "ngrok" in name.lower() or "ngrok" in cmdline.lower():
                    ngrok_processes.append(
                        {
                            "pid": proc.info.get("pid"),
                            "name": name,
                            "cmdline": truncate_text(cmdline, 1000),
                        }
                    )

            except Exception:
                pass

        status["ngrok_processes"] = ngrok_processes

    return status


# ----------------------------
# Desktop operator tools
# ----------------------------

DESKTOP_CONTROL_CONFIRM = "CONTROL_DESKTOP"
LAUNCH_CONFIRM = "LAUNCH_PROGRAM"


def desktop_module_status() -> dict:
    """Returns availability of optional desktop automation modules."""
    return {
        "pyautogui": pyautogui is not None,
        "mss": mss is not None,
        "PIL": Image is not None and ImageDraw is not None,
        "pygetwindow": gw is not None,
        "pywinauto": pywinauto is not None,
        "pytesseract": pytesseract is not None,
    }


def require_desktop_confirm(confirm: str) -> dict | None:
    if confirm != DESKTOP_CONTROL_CONFIRM:
        return {
            "ok": False,
            "error": f"Refusing desktop control. Use confirm='{DESKTOP_CONTROL_CONFIRM}'.",
        }
    return None


def default_screenshot_path(prefix: str = "screen") -> Path:
    folder = SCREENSHOT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return folder / f"{prefix}_{stamp}.png"


def save_screenshot_with_mss(monitor: int, save_path: Path) -> dict:
    if mss is None:
        return {
            "ok": False,
            "error": "mss is not installed.",
            "modules": desktop_module_status(),
        }

    if Image is None:
        return {
            "ok": False,
            "error": "Pillow is not installed.",
            "modules": desktop_module_status(),
        }

    with mss.mss() as sct:
        monitors = sct.monitors

        if monitor < 0 or monitor >= len(monitors):
            return {
                "ok": False,
                "error": f"Invalid monitor index {monitor}. Valid range is 0..{len(monitors)-1}. Monitor 0 is all monitors.",
                "monitors": monitors,
            }

        raw = sct.grab(monitors[monitor])
        img = Image.frombytes("RGB", raw.size, raw.rgb)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path)

        return {
            "ok": True,
            "path": str(save_path),
            "monitor": monitor,
            "width": img.width,
            "height": img.height,
            "monitors": monitors,
        }


@mcp.tool()
def desktop_operator_status() -> dict:
    """Returns availability of desktop automation support modules."""
    return {
        "ok": True,
        "modules": desktop_module_status(),
        "desktop_control_confirm": DESKTOP_CONTROL_CONFIRM,
        "launch_confirm": LAUNCH_CONFIRM,
        "recommended_install": f'"{sys.executable}" -m pip install -r "{PORTAL_HOME / "requirements.txt"}"',
    }


@mcp.tool()
def capture_screen(monitor: int = 0, save_path: str = "") -> dict:
    """Captures the desktop and saves a PNG image. monitor=0 captures all monitors."""
    try:
        p = resolve_path(save_path) if save_path else default_screenshot_path("screen")

        if mss is not None and Image is not None:
            return save_screenshot_with_mss(int(monitor), p)

        if pyautogui is None:
            return {
                "ok": False,
                "error": "No screenshot backend available. Install mss+pillow or pyautogui+pillow.",
                "modules": desktop_module_status(),
            }

        img = pyautogui.screenshot()
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p)

        return {
            "ok": True,
            "path": str(p),
            "monitor": monitor,
            "width": img.width,
            "height": img.height,
            "backend": "pyautogui",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def annotate_screen(
    x: int,
    y: int,
    width: int = 80,
    height: int = 40,
    monitor: int = 0,
    save_path: str = "",
) -> dict:
    """Captures the screen and draws a red rectangle around a target area."""
    try:
        if Image is None or ImageDraw is None:
            return {
                "ok": False,
                "error": "Pillow is not installed.",
                "modules": desktop_module_status(),
            }

        cap = capture_screen(monitor=monitor, save_path="")
        if not cap.get("ok"):
            return cap

        src_img = Image.open(cap["path"])
        draw = ImageDraw.Draw(src_img)

        x = int(x)
        y = int(y)
        width = max(1, int(width))
        height = max(1, int(height))

        draw.rectangle([x, y, x + width, y + height], outline="red", width=6)

        p = resolve_path(save_path) if save_path else default_screenshot_path("annotated")
        p.parent.mkdir(parents=True, exist_ok=True)
        src_img.save(p)

        return {
            "ok": True,
            "path": str(p),
            "source_path": cap["path"],
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def get_mouse_position() -> dict:
    """Returns the current mouse cursor position."""
    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pos = pyautogui.position()
        return {
            "ok": True,
            "x": pos.x,
            "y": pos.y,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def move_mouse(x: int, y: int, duration_seconds: float = 0.1, confirm: str = "") -> dict:
    """Moves the mouse cursor. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.moveTo(int(x), int(y), duration=max(0.0, float(duration_seconds)))
        return {
            "ok": True,
            "x": int(x),
            "y": int(y),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def left_click(x: int, y: int, confirm: str = "") -> dict:
    """Left-clicks at screen coordinates. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.click(int(x), int(y), button="left")
        return {
            "ok": True,
            "x": int(x),
            "y": int(y),
            "button": "left",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def right_click(x: int, y: int, confirm: str = "") -> dict:
    """Right-clicks at screen coordinates. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.click(int(x), int(y), button="right")
        return {
            "ok": True,
            "x": int(x),
            "y": int(y),
            "button": "right",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def double_click(x: int, y: int, confirm: str = "") -> dict:
    """Double-clicks at screen coordinates. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.doubleClick(int(x), int(y), button="left")
        return {
            "ok": True,
            "x": int(x),
            "y": int(y),
            "button": "left",
            "clicks": 2,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def drag_mouse(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_seconds: float = 0.5,
    confirm: str = "",
) -> dict:
    """Drags the mouse from one point to another. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.moveTo(int(x1), int(y1))
        pyautogui.dragTo(int(x2), int(y2), duration=max(0.0, float(duration_seconds)), button="left")
        return {
            "ok": True,
            "from": {"x": int(x1), "y": int(y1)},
            "to": {"x": int(x2), "y": int(y2)},
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def press_key(key: str, presses: int = 1, interval_seconds: float = 0.05, confirm: str = "") -> dict:
    """Presses a keyboard key. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        presses = max(1, min(int(presses), 100))
        pyautogui.press(key, presses=presses, interval=max(0.0, float(interval_seconds)))
        return {
            "ok": True,
            "key": key,
            "presses": presses,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def hotkey(keys_csv: str, confirm: str = "") -> dict:
    """Presses a keyboard shortcut. Example keys_csv='ctrl,shift,s'. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        keys = [k.strip().lower() for k in keys_csv.split(",") if k.strip()]
        if not keys:
            return {
                "ok": False,
                "error": "No keys provided. Use comma-separated keys, for example: ctrl,s",
            }

        pyautogui.hotkey(*keys)
        return {
            "ok": True,
            "keys": keys,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def type_text(text: str, interval_seconds: float = 0.01, confirm: str = "") -> dict:
    """Types text into the active window. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        pyautogui.write(text, interval=max(0.0, float(interval_seconds)))
        return {
            "ok": True,
            "chars_typed": len(text),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


def get_windows_by_title(title_filter: str = "") -> list[dict]:
    title_filter_lower = title_filter.lower().strip()
    results = []

    if gw is not None:
        try:
            for w in gw.getAllWindows():
                title = w.title or ""
                if title_filter_lower and title_filter_lower not in title.lower():
                    continue

                results.append(
                    {
                        "title": title,
                        "left": w.left,
                        "top": w.top,
                        "width": w.width,
                        "height": w.height,
                        "is_active": bool(getattr(w, "isActive", False)),
                        "is_minimized": bool(getattr(w, "isMinimized", False)),
                        "is_maximized": bool(getattr(w, "isMaximized", False)),
                        "backend": "pygetwindow",
                    }
                )
        except Exception:
            pass

    return results


@mcp.tool()
def desktop_windows(title_filter: str = "", max_results: int = 100) -> dict:
    """Lists desktop windows with position and size."""
    try:
        max_results = max(1, min(int(max_results), 500))
        windows = get_windows_by_title(title_filter)[:max_results]

        return {
            "ok": True,
            "title_filter": title_filter,
            "count": len(windows),
            "windows": windows,
            "modules": desktop_module_status(),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def activate_window(title: str) -> dict:
    """Brings the first matching window to the foreground."""
    if gw is None:
        return {
            "ok": False,
            "error": "pygetwindow is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        matches = gw.getWindowsWithTitle(title)

        if not matches:
            return {
                "ok": False,
                "error": "No matching window found.",
                "title": title,
            }

        w = matches[0]
        if getattr(w, "isMinimized", False):
            w.restore()

        w.activate()

        return {
            "ok": True,
            "title": w.title,
            "left": w.left,
            "top": w.top,
            "width": w.width,
            "height": w.height,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": title,
        }


@mcp.tool()
def maximize_window(title: str) -> dict:
    """Maximizes the first matching window."""
    if gw is None:
        return {
            "ok": False,
            "error": "pygetwindow is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        matches = gw.getWindowsWithTitle(title)

        if not matches:
            return {
                "ok": False,
                "error": "No matching window found.",
                "title": title,
            }

        w = matches[0]
        w.maximize()

        return {
            "ok": True,
            "title": w.title,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": title,
        }


@mcp.tool()
def minimize_window(title: str) -> dict:
    """Minimizes the first matching window."""
    if gw is None:
        return {
            "ok": False,
            "error": "pygetwindow is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        matches = gw.getWindowsWithTitle(title)

        if not matches:
            return {
                "ok": False,
                "error": "No matching window found.",
                "title": title,
            }

        w = matches[0]
        w.minimize()

        return {
            "ok": True,
            "title": w.title,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": title,
        }


@mcp.tool()
def close_window(title: str, confirm: str = "") -> dict:
    """Closes the first matching window. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if gw is None:
        return {
            "ok": False,
            "error": "pygetwindow is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        matches = gw.getWindowsWithTitle(title)

        if not matches:
            return {
                "ok": False,
                "error": "No matching window found.",
                "title": title,
            }

        w = matches[0]
        window_title = w.title
        w.close()

        return {
            "ok": True,
            "title": window_title,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": title,
        }


@mcp.tool()
def capture_window(title: str, save_path: str = "") -> dict:
    """Captures the screen area occupied by the first matching window."""
    try:
        windows = get_windows_by_title(title)

        if not windows:
            return {
                "ok": False,
                "error": "No matching window found.",
                "title": title,
                "modules": desktop_module_status(),
            }

        w = windows[0]
        cap = capture_screen(monitor=0, save_path="")

        if not cap.get("ok"):
            return cap

        if Image is None:
            return {
                "ok": False,
                "error": "Pillow is not installed.",
                "modules": desktop_module_status(),
            }

        img = Image.open(cap["path"])
        left = max(0, int(w["left"]))
        top = max(0, int(w["top"]))
        right = max(left + 1, left + int(w["width"]))
        bottom = max(top + 1, top + int(w["height"]))

        cropped = img.crop((left, top, right, bottom))

        p = resolve_path(save_path) if save_path else default_screenshot_path("window")
        p.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(p)

        return {
            "ok": True,
            "path": str(p),
            "title": w["title"],
            "bounds": {
                "left": left,
                "top": top,
                "width": int(w["width"]),
                "height": int(w["height"]),
            },
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": title,
        }


@mcp.tool()
def list_ui_elements(window_title: str = "", control_type: str = "", max_results: int = 200) -> dict:
    """Lists visible UI Automation elements for a matching window. Best for buttons, menus, edit boxes, tabs."""
    if Desktop is None:
        return {
            "ok": False,
            "error": "pywinauto is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        max_results = max(1, min(int(max_results), 2000))
        results = []
        control_type_filter = control_type.lower().strip()
        title_filter = window_title.lower().strip()

        desktop = Desktop(backend="uia")
        windows = desktop.windows()

        for w in windows:
            try:
                title = w.window_text() or ""
                if title_filter and title_filter not in title.lower():
                    continue

                for elem in w.descendants():
                    if len(results) >= max_results:
                        break

                    try:
                        info = elem.element_info
                        name = info.name or ""
                        ctype = info.control_type or ""

                        if control_type_filter and control_type_filter not in ctype.lower():
                            continue

                        rect = info.rectangle

                        results.append(
                            {
                                "window_title": title,
                                "name": name,
                                "control_type": ctype,
                                "automation_id": info.automation_id,
                                "class_name": info.class_name,
                                "rectangle": {
                                    "left": rect.left,
                                    "top": rect.top,
                                    "right": rect.right,
                                    "bottom": rect.bottom,
                                    "width": rect.width(),
                                    "height": rect.height(),
                                },
                            }
                        )

                    except Exception:
                        pass

                if len(results) >= max_results:
                    break

            except Exception:
                pass

        return {
            "ok": True,
            "window_title": window_title,
            "control_type": control_type,
            "count": len(results),
            "elements": results,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def click_ui_element(
    window_title: str,
    element_name: str,
    occurrence: int = 1,
    control_type: str = "",
    confirm: str = "",
) -> dict:
    """Clicks a UI Automation element by name. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if Desktop is None:
        return {
            "ok": False,
            "error": "pywinauto is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        occurrence = max(1, int(occurrence))
        target_name = element_name.lower().strip()
        title_filter = window_title.lower().strip()
        control_type_filter = control_type.lower().strip()
        hit_count = 0

        desktop = Desktop(backend="uia")

        for w in desktop.windows():
            try:
                title = w.window_text() or ""
                if title_filter and title_filter not in title.lower():
                    continue

                try:
                    w.set_focus()
                except Exception:
                    pass

                for elem in w.descendants():
                    try:
                        info = elem.element_info
                        name = (info.name or "").strip()
                        ctype = info.control_type or ""

                        if target_name not in name.lower():
                            continue

                        if control_type_filter and control_type_filter not in ctype.lower():
                            continue

                        hit_count += 1

                        if hit_count == occurrence:
                            rect = info.rectangle
                            x = int((rect.left + rect.right) / 2)
                            y = int((rect.top + rect.bottom) / 2)

                            try:
                                elem.click_input()
                            except Exception:
                                if pyautogui is None:
                                    raise
                                pyautogui.click(x, y)

                            return {
                                "ok": True,
                                "window_title": title,
                                "element_name": name,
                                "control_type": ctype,
                                "x": x,
                                "y": y,
                            }

                    except Exception:
                        pass

            except Exception:
                pass

        return {
            "ok": False,
            "error": "Matching UI element not found.",
            "window_title": window_title,
            "element_name": element_name,
            "occurrence": occurrence,
            "control_type": control_type,
            "matches_seen": hit_count,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def ocr_screen(monitor: int = 0, save_path: str = "") -> dict:
    """Runs OCR on a screenshot and returns detected text blocks. Requires pytesseract installed and configured."""
    if pytesseract is None:
        return {
            "ok": False,
            "error": "pytesseract is not installed. Also requires the Tesseract OCR engine installed on Windows.",
            "modules": desktop_module_status(),
        }

    if Image is None:
        return {
            "ok": False,
            "error": "Pillow is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        cap = capture_screen(monitor=monitor, save_path=save_path)

        if not cap.get("ok"):
            return cap

        img = Image.open(cap["path"])
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        blocks = []
        n = len(data.get("text", []))

        for i in range(n):
            text = (data["text"][i] or "").strip()

            if not text:
                continue

            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1.0

            blocks.append(
                {
                    "text": text,
                    "confidence": conf,
                    "left": int(data["left"][i]),
                    "top": int(data["top"][i]),
                    "width": int(data["width"][i]),
                    "height": int(data["height"][i]),
                }
            )

        return {
            "ok": True,
            "image_path": cap["path"],
            "count": len(blocks),
            "blocks": blocks,
            "full_text": truncate_text(pytesseract.image_to_string(img), 10000),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def find_text_on_screen(text: str, occurrence: int = 1, monitor: int = 0) -> dict:
    """Finds text on screen using OCR and returns an approximate bounding box."""
    try:
        occurrence = max(1, int(occurrence))
        target = text.lower().strip()

        if not target:
            return {
                "ok": False,
                "error": "No text provided.",
            }

        ocr = ocr_screen(monitor=monitor)

        if not ocr.get("ok"):
            return ocr

        matches = []

        for block in ocr.get("blocks", []):
            if target in block.get("text", "").lower():
                matches.append(block)

        if len(matches) < occurrence:
            return {
                "ok": False,
                "error": "Text not found.",
                "text": text,
                "occurrence": occurrence,
                "matches_found": len(matches),
                "image_path": ocr.get("image_path"),
            }

        hit = matches[occurrence - 1]
        hit["ok"] = True
        hit["text_searched"] = text
        hit["x"] = hit["left"] + hit["width"] // 2
        hit["y"] = hit["top"] + hit["height"] // 2
        hit["image_path"] = ocr.get("image_path")

        return hit

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def click_text(text: str, occurrence: int = 1, monitor: int = 0, confirm: str = "") -> dict:
    """Finds visible text with OCR and clicks it. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        hit = find_text_on_screen(text=text, occurrence=occurrence, monitor=monitor)

        if not hit.get("ok"):
            return hit

        x = int(hit["x"])
        y = int(hit["y"])
        pyautogui.click(x, y)

        return {
            "ok": True,
            "text": text,
            "occurrence": occurrence,
            "x": x,
            "y": y,
            "confidence": hit.get("confidence"),
            "image_path": hit.get("image_path"),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def find_image_on_screen(
    image_path: str,
    confidence: float = 0.8,
    monitor: int = 0,
) -> dict:
    """Finds an image/template on screen. Requires pyautogui and usually OpenCV for confidence matching."""
    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    try:
        p = resolve_path(image_path)

        if not p.exists():
            return {
                "ok": False,
                "error": "Image path does not exist.",
                "image_path": str(p),
            }

        try:
            box = pyautogui.locateOnScreen(str(p), confidence=float(confidence))
        except TypeError:
            box = pyautogui.locateOnScreen(str(p))

        if box is None:
            return {
                "ok": False,
                "found": False,
                "image_path": str(p),
                "confidence": confidence,
            }

        x = box.left + box.width // 2
        y = box.top + box.height // 2

        return {
            "ok": True,
            "found": True,
            "image_path": str(p),
            "left": box.left,
            "top": box.top,
            "width": box.width,
            "height": box.height,
            "x": x,
            "y": y,
            "confidence": confidence,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "modules": desktop_module_status(),
        }


@mcp.tool()
def click_image_on_screen(
    image_path: str,
    confidence: float = 0.8,
    confirm: str = "",
) -> dict:
    """Finds an image/template on screen and clicks its center. Requires confirm='CONTROL_DESKTOP'."""
    refusal = require_desktop_confirm(confirm)
    if refusal:
        return refusal

    if pyautogui is None:
        return {
            "ok": False,
            "error": "pyautogui is not installed.",
            "modules": desktop_module_status(),
        }

    hit = find_image_on_screen(image_path=image_path, confidence=confidence)

    if not hit.get("ok"):
        return hit

    pyautogui.click(int(hit["x"]), int(hit["y"]))

    hit["clicked"] = True
    return hit


@mcp.tool()
def wait_for_window(title: str, timeout_seconds: int = 30) -> dict:
    """Waits until a window with matching title appears."""
    try:
        timeout_seconds = max(1, min(int(timeout_seconds), 300))
        end = time.time() + timeout_seconds

        while time.time() < end:
            windows = get_windows_by_title(title)

            if windows:
                return {
                    "ok": True,
                    "title": title,
                    "matched_window": windows[0],
                    "seconds_waited": round(timeout_seconds - (end - time.time()), 2),
                }

            time.sleep(0.5)

        return {
            "ok": False,
            "error": "Timed out waiting for window.",
            "title": title,
            "timeout_seconds": timeout_seconds,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def launch_program(
    exe: str,
    args: str = "",
    cwd: str = "",
    confirm: str = "",
) -> dict:
    """Launches a program. Requires confirm='LAUNCH_PROGRAM'."""
    try:
        if confirm != LAUNCH_CONFIRM:
            return {
                "ok": False,
                "error": f"Refusing to launch program. Use confirm='{LAUNCH_CONFIRM}'.",
            }

        exe = exe.strip()

        if not exe:
            return {
                "ok": False,
                "error": "No executable provided.",
            }

        cwd_path = str(resolve_path(cwd)) if cwd else None

        if cwd_path and not Path(cwd_path).exists():
            return {
                "ok": False,
                "error": "Working directory does not exist.",
                "cwd": cwd_path,
            }

        if args:
            command = f'Start-Process -FilePath "{exe}" -ArgumentList "{args}"'
        else:
            command = f'Start-Process -FilePath "{exe}"'

        result = run_process(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            cwd=cwd_path,
            timeout_seconds=30,
        )

        result["exe"] = exe
        result["args"] = args
        result["cwd"] = cwd_path

        return result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def launch_start_app(name: str, confirm: str = "") -> dict:
    """Launches an installed Start Menu app by display name match. Requires confirm='LAUNCH_PROGRAM'."""
    try:
        if confirm != LAUNCH_CONFIRM:
            return {
                "ok": False,
                "error": f"Refusing to launch app. Use confirm='{LAUNCH_CONFIRM}'.",
            }

        ps = (
            "$app = Get-StartApps | Where-Object { $_.Name -match "
            + repr(name)
            + " } | Select-Object -First 1; "
            "$app | ConvertTo-Json -Depth 3; "
            "if ($app) { Start-Process \"shell:AppsFolder\\$($app.AppID)\" }"
        )

        result = run_process(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps,
            ],
            cwd=str(PORTAL_HOME),
            timeout_seconds=30,
        )

        result["name"] = name

        return result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def computer_help() -> dict:
    """Lists examples for using the desktop operator tools."""
    return {
        "ok": True,
        "examples": [
            "capture_screen()",
            "desktop_windows(title_filter='Photoshop')",
            "activate_window(title='Photoshop')",
            "annotate_screen(x=100, y=200, width=300, height=100)",
            "left_click(x=100, y=200, confirm='CONTROL_DESKTOP')",
            "hotkey(keys_csv='ctrl,s', confirm='CONTROL_DESKTOP')",
            "type_text(text='example', confirm='CONTROL_DESKTOP')",
            "list_ui_elements(window_title='Photoshop', control_type='Button')",
            "click_ui_element(window_title='Photoshop', element_name='OK', confirm='CONTROL_DESKTOP')",
            "ocr_screen()",
            "click_text(text='Layers', confirm='CONTROL_DESKTOP')",
            "launch_start_app(name='Adobe Photoshop 2025', confirm='LAUNCH_PROGRAM')",
        ],
        "notes": [
            "Use capture_screen first so ChatGPT can see the desktop before clicking.",
            "Use UI Automation when possible; OCR is fallback and requires Tesseract OCR installed.",
            "Mouse/keyboard tools require confirm='CONTROL_DESKTOP'.",
            "Launch tools require confirm='LAUNCH_PROGRAM'.",
        ],
        "modules": desktop_module_status(),
    }



@mcp.tool()
def list_available_paths(include_common_folders: bool = True) -> dict:
    """
    Lists filesystem roots visible to the Portal Windows account.

    Portal does not impose a drive allowlist: any absolute or relative path
    visible to this Windows account can be passed to the path-based tools.
    """
    try:
        drives = []
        partition_by_mount = {}

        if psutil is not None:
            try:
                for part in psutil.disk_partitions(all=True):
                    key = str(part.mountpoint).rstrip("\\/").lower()
                    partition_by_mount[key] = part
            except Exception:
                partition_by_mount = {}

        if os.name == "nt":
            roots = [Path(f"{chr(code)}:\\") for code in range(ord("A"), ord("Z") + 1)]
        else:
            roots = [Path("/")]

        for root in roots:
            try:
                if not root.exists():
                    continue

                usage = shutil.disk_usage(root)
                key = str(root).rstrip("\\/").lower()
                part = partition_by_mount.get(key)

                drives.append(
                    {
                        "path": str(root),
                        "accessible": True,
                        "filesystem": getattr(part, "fstype", "") if part else "",
                        "device": getattr(part, "device", "") if part else "",
                        "total_gb": round(usage.total / (1024 ** 3), 2),
                        "free_gb": round(usage.free / (1024 ** 3), 2),
                        "readable": os.access(root, os.R_OK),
                        "writable": os.access(root, os.W_OK),
                    }
                )
            except Exception as e:
                drives.append(
                    {
                        "path": str(root),
                        "accessible": False,
                        "error": str(e),
                    }
                )

        common_folders = []
        if include_common_folders:
            candidates = [
                ("home", Path.home()),
                ("desktop", Path.home() / "Desktop"),
                ("documents", Path.home() / "Documents"),
                ("downloads", Path.home() / "Downloads"),
                ("pictures", Path.home() / "Pictures"),
                ("videos", Path.home() / "Videos"),
                ("portal", PORTAL_HOME),
            ]

            for name, folder in candidates:
                common_folders.append(
                    {
                        "name": name,
                        "path": str(folder),
                        "exists": folder.exists(),
                        "readable": folder.exists() and os.access(folder, os.R_OK),
                        "writable": folder.exists() and os.access(folder, os.W_OK),
                    }
                )

        return {
            "ok": True,
            "path_policy": (
                "No Portal drive allowlist. Paths are limited only by what the "
                "Portal Windows account and operating system can access."
            ),
            "working_directory": os.getcwd(),
            "drives": drives,
            "common_folders": common_folders,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def path_access(path: str) -> dict:
    """
    Resolves a path and reports whether the Portal account can access it.
    This check does not create, change, or delete anything.
    """
    try:
        p = resolve_path(path)
        exists = p.exists()
        probe = p if exists else p.parent

        while not probe.exists() and probe != probe.parent:
            probe = probe.parent

        result = {
            "ok": True,
            "requested_path": path,
            "resolved_path": str(p),
            "exists": exists,
            "nearest_existing_parent": str(probe),
            "parent_readable": os.access(probe, os.R_OK),
            "parent_writable": os.access(probe, os.W_OK),
        }

        if exists:
            st = p.stat()
            result.update(
                {
                    "is_file": p.is_file(),
                    "is_directory": p.is_dir(),
                    "readable": os.access(p, os.R_OK),
                    "writable": os.access(p, os.W_OK),
                    "size_bytes": st.st_size,
                    "created": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(st.st_ctime)
                    ),
                    "modified": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)
                    ),
                }
            )

        return result

    except Exception as e:
        return {
            "ok": False,
            "requested_path": path,
            "error": str(e),
        }


@mcp.tool()
def read_text_range(
    path: str,
    start_line: int = 1,
    max_lines: int = 500,
    max_chars: int = 50000,
) -> dict:
    """
    Reads a bounded line range from a text file on any accessible path.
    Use next_start_line to continue through files larger than one tool result.
    """
    try:
        p = resolve_path(path)
        start_line = max(1, int(start_line))
        max_lines = max(1, min(int(max_lines), 5000))
        max_chars = max(1, min(int(max_chars), 100000))

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "File does not exist.",
            }

        if not p.is_file():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path is not a file.",
            }

        selected = []
        chars = 0
        end_line = start_line - 1
        has_more = False
        partial_line = False

        with open(p, "r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line_number < start_line:
                    continue

                if len(selected) >= max_lines:
                    has_more = True
                    break

                if chars + len(line) > max_chars:
                    if not selected:
                        selected.append(line[:max_chars])
                        chars = max_chars
                        end_line = line_number
                        partial_line = True
                    has_more = True
                    break

                selected.append(line)
                chars += len(line)
                end_line = line_number

        if has_more:
            next_start_line = end_line if partial_line else end_line + 1
        else:
            next_start_line = None

        return {
            "ok": True,
            "path": str(p),
            "start_line": start_line,
            "end_line": end_line,
            "lines_returned": len(selected),
            "chars_returned": chars,
            "has_more": has_more,
            "next_start_line": next_start_line,
            "partial_line": partial_line,
            "content": "".join(selected),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def hash_file(
    path: str,
    algorithm: str = "sha256",
    chunk_size_mb: int = 8,
) -> dict:
    """Hashes a file on any accessible path without changing it."""
    try:
        import hashlib

        p = resolve_path(path)
        algorithm = str(algorithm).strip().lower()
        allowed_algorithms = {"md5", "sha1", "sha256", "sha512"}

        if algorithm not in allowed_algorithms:
            return {
                "ok": False,
                "error": "algorithm must be one of: md5, sha1, sha256, sha512.",
            }

        if not p.exists():
            return {
                "ok": False,
                "path": str(p),
                "error": "File does not exist.",
            }

        if not p.is_file():
            return {
                "ok": False,
                "path": str(p),
                "error": "Path is not a file.",
            }

        chunk_size_mb = max(1, min(int(chunk_size_mb), 64))
        digest = hashlib.new(algorithm)
        started = time.perf_counter()

        with open(p, "rb") as handle:
            while True:
                chunk = handle.read(chunk_size_mb * 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)

        elapsed = time.perf_counter() - started

        return {
            "ok": True,
            "path": str(p),
            "algorithm": algorithm,
            "hash": digest.hexdigest(),
            "size_bytes": p.stat().st_size,
            "elapsed_seconds": round(elapsed, 3),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


# Persistent multi-process job manager.
# Each job runs in its own worker process and writes separate metadata/output files.
import json as _job_json
import re as _job_re
import uuid as _job_uuid

JOB_ROOT = Path(os.getenv("PORTAL_JOB_DIR", str(PORTAL_HOME / "jobs"))).resolve()
_JOB_ID_PATTERN = _job_re.compile(r"^[0-9]{8}_[0-9]{6}_[a-f0-9]{8}$")
_JOB_TERMINAL_STATES = {"completed", "failed", "stopped", "timed_out", "orphaned"}


def _job_now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _job_dir(job_id):
    job_id = str(job_id).strip().lower()

    if not _JOB_ID_PATTERN.fullmatch(job_id):
        raise ValueError("Invalid job ID.")

    root = JOB_ROOT.resolve()
    folder = (root / job_id).resolve()

    if root not in folder.parents:
        raise ValueError("Job path escaped the job root.")

    return folder


def _job_meta_path(job_id):
    return _job_dir(job_id) / "job.json"


def _job_write_meta(job_id, data):
    folder = _job_dir(job_id)
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / "job.json"
    temporary = folder / "job.json.tmp"

    with open(temporary, "w", encoding="utf-8") as handle:
        _job_json.dump(data, handle, indent=2, ensure_ascii=False)

    os.replace(temporary, destination)


def _job_read_meta(job_id):
    path = _job_meta_path(job_id)

    if not path.exists():
        raise FileNotFoundError(f"Unknown job ID: {job_id}")

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return _job_json.load(handle)


def _job_process_alive(pid, expected_create_time=None):
    if not pid:
        return False

    if psutil is None:
        return None

    try:
        proc = psutil.Process(int(pid))

        if expected_create_time is not None:
            if abs(proc.create_time() - float(expected_create_time)) > 2.0:
                return False

        zombie = getattr(psutil, "STATUS_ZOMBIE", "zombie")
        return proc.is_running() and proc.status() != zombie
    except Exception:
        return False


def _job_tail(path, lines=100, max_chars=20000):
    lines = max(1, min(int(lines), 5000))
    max_chars = max(1, min(int(max_chars), 100000))
    p = Path(path)

    if not p.exists() or not p.is_file():
        return ""

    try:
        read_bytes = max_chars * 4

        with open(p, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - read_bytes), os.SEEK_SET)
            data = handle.read()

        text = data.decode("utf-8", errors="replace")
        selected = "\n".join(text.splitlines()[-lines:])
        return selected[-max_chars:]
    except Exception as e:
        return f"[Could not read job output: {e}]"


def _job_snapshot(meta, include_output=False, tail_lines=40, max_chars=12000):
    result = dict(meta)
    worker_alive = _job_process_alive(
        meta.get("worker_pid"),
        meta.get("worker_create_time"),
    )
    process_alive = _job_process_alive(
        meta.get("process_pid"),
        meta.get("process_create_time"),
    )

    result["worker_alive"] = worker_alive
    result["process_alive"] = process_alive
    result["effective_status"] = meta.get("status", "unknown")

    if (
        result["effective_status"] in {"starting", "running", "stopping"}
        and worker_alive is False
        and process_alive is False
    ):
        result["effective_status"] = "orphaned"
        result["warning"] = (
            "Neither the worker nor command process is running, but no normal "
            "completion record was written."
        )

    if include_output:
        result["stdout_tail"] = _job_tail(
            meta.get("stdout_path", ""),
            lines=tail_lines,
            max_chars=max_chars,
        )
        result["stderr_tail"] = _job_tail(
            meta.get("stderr_path", ""),
            lines=tail_lines,
            max_chars=max_chars,
        )

    return result


def _run_portal_job_worker(job_id):
    try:
        meta = _job_read_meta(job_id)
    except Exception:
        return 2

    folder = _job_dir(job_id)
    stdout_path = folder / "stdout.log"
    stderr_path = folder / "stderr.log"
    worker_pid = os.getpid()
    worker_create_time = None

    if psutil is not None:
        try:
            worker_create_time = psutil.Process(worker_pid).create_time()
        except Exception:
            pass

    meta.update(
        {
            "status": "running",
            "worker_pid": worker_pid,
            "worker_create_time": worker_create_time,
            "started_at": _job_now(),
        }
    )
    _job_write_meta(job_id, meta)

    shell = meta.get("shell", "powershell")
    command = meta.get("command", "")
    cwd = meta.get("cwd") or str(PORTAL_HOME)
    timeout_seconds = int(meta.get("timeout_seconds", 0) or 0)

    if shell == "powershell":
        args = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ]
    else:
        args = [
            "cmd.exe",
            "/d",
            "/c",
            command,
        ]

    creation_flags = 0
    if os.name == "nt":
        creation_flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creation_flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

    final_status = "failed"
    exit_code = None
    error = None

    try:
        with open(stdout_path, "ab", buffering=0) as stdout_handle:
            with open(stderr_path, "ab", buffering=0) as stderr_handle:
                proc = subprocess.Popen(
                    args,
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    creationflags=creation_flags,
                )

                process_create_time = None
                if psutil is not None:
                    try:
                        process_create_time = psutil.Process(proc.pid).create_time()
                    except Exception:
                        pass

                meta = _job_read_meta(job_id)
                meta.update(
                    {
                        "status": "running",
                        "process_pid": proc.pid,
                        "process_create_time": process_create_time,
                    }
                )
                _job_write_meta(job_id, meta)

                try:
                    if timeout_seconds > 0:
                        exit_code = proc.wait(timeout=timeout_seconds)
                    else:
                        exit_code = proc.wait()

                    final_status = "completed" if exit_code == 0 else "failed"

                except subprocess.TimeoutExpired:
                    final_status = "timed_out"
                    error = f"Job exceeded its {timeout_seconds}-second timeout."

                    if os.name == "nt":
                        subprocess.run(
                            [
                                "taskkill.exe",
                                "/PID",
                                str(proc.pid),
                                "/T",
                                "/F",
                            ],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=30,
                        )
                    else:
                        proc.kill()

                    try:
                        exit_code = proc.wait(timeout=10)
                    except Exception:
                        exit_code = None

    except Exception as e:
        error = str(e)

        try:
            with open(stderr_path, "a", encoding="utf-8", errors="replace") as handle:
                handle.write(f"\nPortal job worker error: {e}\n")
        except Exception:
            pass

    try:
        meta = _job_read_meta(job_id)

        if meta.get("status") != "stopped":
            meta.update(
                {
                    "status": final_status,
                    "exit_code": exit_code,
                    "finished_at": _job_now(),
                }
            )

            if error:
                meta["error"] = error

            _job_write_meta(job_id, meta)
    except Exception:
        pass

    return 0 if final_status == "completed" else 1


@mcp.tool()
def start_job(
    command: str,
    shell: str = "powershell",
    cwd: str = "",
    timeout_seconds: int = 0,
    confirm: str = "",
) -> dict:
    """
    Starts an independently monitored background job and returns immediately.

    Use confirm='START_JOB' for read-only commands.
    Commands detected as mutating require confirm='START_MUTATING_JOB'.
    Blocked destructive commands are always refused.
    timeout_seconds=0 means no automatic timeout; otherwise the maximum is 86400.
    """
    try:
        command = str(command).strip()
        shell = str(shell).strip().lower()

        if not command:
            return {
                "ok": False,
                "error": "No command provided.",
            }

        if shell not in {"powershell", "cmd"}:
            return {
                "ok": False,
                "error": "shell must be 'powershell' or 'cmd'.",
            }

        if command_is_blocked(command):
            return {
                "ok": False,
                "error": "Blocked dangerous command.",
            }

        needs_mutating_confirm = command_needs_confirm(command)
        expected_confirm = (
            "START_MUTATING_JOB" if needs_mutating_confirm else "START_JOB"
        )

        if confirm != expected_confirm:
            return {
                "ok": False,
                "error": f"Refusing to start job. Use confirm='{expected_confirm}'.",
                "mutating_command_detected": needs_mutating_confirm,
            }

        cwd_path = resolve_path(cwd or str(PORTAL_HOME))

        if not cwd_path.exists() or not cwd_path.is_dir():
            return {
                "ok": False,
                "error": "Working directory does not exist or is not a directory.",
                "cwd": str(cwd_path),
            }

        timeout_seconds = max(0, min(int(timeout_seconds), 86400))
        JOB_ROOT.mkdir(parents=True, exist_ok=True)
        job_id = (
            time.strftime("%Y%m%d_%H%M%S", time.localtime())
            + "_"
            + _job_uuid.uuid4().hex[:8]
        )
        folder = _job_dir(job_id)
        folder.mkdir(parents=True, exist_ok=False)
        stdout_path = folder / "stdout.log"
        stderr_path = folder / "stderr.log"

        stdout_path.touch()
        stderr_path.touch()

        meta = {
            "job_id": job_id,
            "status": "starting",
            "command": command,
            "shell": shell,
            "cwd": str(cwd_path),
            "timeout_seconds": timeout_seconds,
            "created_at": _job_now(),
            "started_at": None,
            "finished_at": None,
            "worker_pid": None,
            "worker_create_time": None,
            "process_pid": None,
            "process_create_time": None,
            "exit_code": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
        _job_write_meta(job_id, meta)

        creation_flags = 0
        if os.name == "nt":
            creation_flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            creation_flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

        worker = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--run-portal-job",
                job_id,
            ],
            cwd=str(cwd_path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creation_flags,
        )

        worker_create_time = None
        if psutil is not None:
            try:
                worker_create_time = psutil.Process(worker.pid).create_time()
            except Exception:
                pass

        meta["worker_pid"] = worker.pid
        meta["worker_create_time"] = worker_create_time
        _job_write_meta(job_id, meta)

        return {
            "ok": True,
            "job_id": job_id,
            "status": "starting",
            "worker_pid": worker.pid,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "message": "Background job started. Use job_status or job_output to monitor it.",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def list_jobs(
    status_filter: str = "",
    max_results: int = 100,
) -> dict:
    """Lists persistent background jobs, newest first."""
    try:
        status_filter = str(status_filter).strip().lower()
        max_results = max(1, min(int(max_results), 1000))

        if not JOB_ROOT.exists():
            return {
                "ok": True,
                "count": 0,
                "jobs": [],
                "job_root": str(JOB_ROOT),
            }

        jobs = []

        for folder in sorted(JOB_ROOT.iterdir(), key=lambda p: p.name, reverse=True):
            if not folder.is_dir() or not _JOB_ID_PATTERN.fullmatch(folder.name):
                continue

            try:
                snapshot = _job_snapshot(_job_read_meta(folder.name))

                if status_filter and snapshot.get("effective_status") != status_filter:
                    continue

                jobs.append(snapshot)

                if len(jobs) >= max_results:
                    break
            except Exception:
                continue

        return {
            "ok": True,
            "count": len(jobs),
            "jobs": jobs,
            "job_root": str(JOB_ROOT),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@mcp.tool()
def job_status(
    job_id: str,
    include_output: bool = True,
    tail_lines: int = 40,
    max_chars: int = 12000,
) -> dict:
    """Returns live status and optional output tails for one background job."""
    try:
        meta = _job_read_meta(job_id)
        result = _job_snapshot(
            meta,
            include_output=bool(include_output),
            tail_lines=tail_lines,
            max_chars=max_chars,
        )
        result["ok"] = True
        return result

    except Exception as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": str(e),
        }


@mcp.tool()
def job_output(
    job_id: str,
    stream: str = "both",
    lines: int = 200,
    max_chars: int = 30000,
) -> dict:
    """Reads bounded stdout and/or stderr tails from a background job."""
    try:
        meta = _job_read_meta(job_id)
        stream = str(stream).strip().lower()

        if stream not in {"stdout", "stderr", "both"}:
            return {
                "ok": False,
                "error": "stream must be 'stdout', 'stderr', or 'both'.",
            }

        result = {
            "ok": True,
            "job_id": job_id,
            "status": meta.get("status"),
            "stream": stream,
        }

        if stream in {"stdout", "both"}:
            result["stdout"] = _job_tail(
                meta.get("stdout_path", ""),
                lines=lines,
                max_chars=max_chars,
            )

        if stream in {"stderr", "both"}:
            result["stderr"] = _job_tail(
                meta.get("stderr_path", ""),
                lines=lines,
                max_chars=max_chars,
            )

        return result

    except Exception as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": str(e),
        }


@mcp.tool()
def stop_job(job_id: str, confirm: str = "") -> dict:
    """
    Stops only the process tree recorded for one Portal job.
    Requires confirm='STOP_JOB'.
    """
    try:
        if confirm != "STOP_JOB":
            return {
                "ok": False,
                "error": "Refusing to stop job. Use confirm='STOP_JOB'.",
            }

        meta = _job_read_meta(job_id)
        snapshot = _job_snapshot(meta)

        if snapshot.get("effective_status") in _JOB_TERMINAL_STATES:
            return {
                "ok": True,
                "job_id": job_id,
                "status": snapshot.get("effective_status"),
                "message": "Job is not running.",
            }

        targets = []
        for pid_key, time_key in [
            ("worker_pid", "worker_create_time"),
            ("process_pid", "process_create_time"),
        ]:
            pid = meta.get(pid_key)
            create_time = meta.get(time_key)

            if pid and _job_process_alive(pid, create_time):
                targets.append(int(pid))

        stopped = []

        for pid in targets:
            try:
                if os.name == "nt":
                    result = subprocess.run(
                        [
                            "taskkill.exe",
                            "/PID",
                            str(pid),
                            "/T",
                            "/F",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        stopped.append(pid)
                elif psutil is not None:
                    psutil.Process(pid).kill()
                    stopped.append(pid)
            except Exception:
                pass

        meta = _job_read_meta(job_id)
        meta.update(
            {
                "status": "stopped",
                "finished_at": _job_now(),
                "stopped_pids": stopped,
            }
        )
        _job_write_meta(job_id, meta)

        return {
            "ok": True,
            "job_id": job_id,
            "status": "stopped",
            "stopped_pids": stopped,
        }

    except Exception as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": str(e),
        }


@mcp.tool()
def delete_job(job_id: str, confirm: str = "") -> dict:
    """
    Deletes the metadata and logs for a finished Portal job.
    Requires confirm='DELETE_JOB'. Running jobs cannot be deleted.
    """
    try:
        if confirm != "DELETE_JOB":
            return {
                "ok": False,
                "error": "Refusing to delete job record. Use confirm='DELETE_JOB'.",
            }

        meta = _job_read_meta(job_id)
        snapshot = _job_snapshot(meta)

        if snapshot.get("worker_alive") or snapshot.get("process_alive"):
            return {
                "ok": False,
                "job_id": job_id,
                "error": "Job is still running. Stop it first.",
            }

        folder = _job_dir(job_id)
        shutil.rmtree(folder)

        return {
            "ok": True,
            "job_id": job_id,
            "deleted_path": str(folder),
        }

    except Exception as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": str(e),
        }

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--run-portal-job":
        sys.exit(_run_portal_job_worker(sys.argv[2]))
    print("About to start MCP...")
    print(f"Local MCP URL: http://127.0.0.1:{PORT}/mcp")
    if HOSTNAME:
        print(f"Configured public MCP URL: https://{HOSTNAME}/mcp")
    else:
        print("Public hostname is not configured (recommended with Secure MCP Tunnel).")
    mcp.run(transport="streamable-http")
