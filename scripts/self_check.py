from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PORTAL_HOME", str(ROOT))
os.environ.setdefault("PORTAL_BIND_HOST", "127.0.0.1")
os.environ.setdefault("PORTAL_PORT", "8000")

from portal import server  # noqa: E402


def main() -> int:
    tool_manager = getattr(server.mcp, "_tool_manager", None)
    tools = getattr(tool_manager, "_tools", {})
    required = {
        "portal_status",
        "read_text_file",
        "write_text_file",
        "run_powershell",
        "capture_screen",
        "desktop_windows",
        "launch_program",
    }
    missing = sorted(required.difference(tools))

    assert server.HOST == "127.0.0.1", "Default bind host must remain loopback-only."
    assert server.PORT == 8000, "Unexpected default port."
    assert len(tools) >= 50, f"Expected at least 50 tools, found {len(tools)}."
    assert not missing, f"Missing required tools: {', '.join(missing)}"

    source = Path(server.__file__).read_text(encoding="utf-8")
    forbidden = (
        "Robert" + "'s PC",
        "ngrok-free" + ".dev",
        "C:\\AI" + "\\Relay",
    )
    hits = [item for item in forbidden if item in source]
    assert not hits, f"Machine-specific values found: {', '.join(hits)}"

    print(f"PASS: {len(tools)} MCP tools registered; loopback-only default verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
