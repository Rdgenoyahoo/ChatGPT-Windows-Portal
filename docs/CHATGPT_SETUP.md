# Connect the Portal to ChatGPT

This guide follows OpenAI's current [Connect from ChatGPT](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt) and [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) documentation.

## Before connecting

Confirm all of these are true:

- `Start-Portal.bat` is running and shows `http://127.0.0.1:8000/mcp`.
- `Start-Portal-and-Tunnel.bat` completed `tunnel-client doctor --explain` successfully.
- The local tunnel status UI at `http://127.0.0.1:8080/ui` reports healthy and ready.
- The tunnel is associated with the target ChatGPT workspace.
- Your runtime key principal and ChatGPT operator have **Tunnels Read + Use**.
- ChatGPT Developer mode is enabled.

## Create the app

1. Go to [chatgpt.com/plugins](https://chatgpt.com/plugins) or open **Settings → Plugins**.
2. Select the plus button.
3. Enter:
   - **Name:** `Windows Portal`
   - **Description:** `Private tools for diagnosing and operating my Windows PC, including files, commands, screenshots, and desktop control.`
4. Choose **Tunnel** under Connection.
5. Select the tunnel from the list, or paste its `tunnel_...` ID.
6. Create the app and confirm that ChatGPT displays the advertised tools.
7. Set the app permission to **Always ask** during initial testing.

## Use it in a chat

1. Start a new ChatGPT conversation.
2. Select the plus button near the composer, then **More**.
3. Select **Windows Portal**.
4. Ask: `Use Windows Portal to call portal_status and system_summary. Do not change anything.`

Next, test a screenshot:

```text
Use Windows Portal to capture the desktop and list the open windows. Do not click or type anything.
```

Only after read-only tests work should you try a write, launch, mouse, or keyboard action.

## Permission levels

ChatGPT currently provides these app permission levels:

- **Always ask** — safest starting point; asks before reads and changes.
- **Ask before making changes** — read-only calls can run automatically.
- **Ask only before important changes** — routine changes may run automatically.

Because this Portal can control the entire interactive Windows session, **Always ask** or **Ask before making changes** is recommended.

## Refresh after an update

When tools or their descriptions change:

1. Restart `Start-Portal-and-Tunnel.bat`.
2. Open the app under **Settings → Plugins**.
3. Select **Refresh**.
4. Confirm the updated tool list.

## If the tunnel is missing

Check these in order:

1. The selected Platform organization is the one that owns the tunnel.
2. The tunnel includes the target ChatGPT workspace association.
3. Your role includes **Tunnels Read + Use**.
4. ChatGPT Developer mode is allowed by the workspace administrator.
5. Wait for a newly granted role to propagate; OpenAI notes this can take up to 30 minutes.

## If tool discovery fails

Keep the Portal terminal open, then rerun:

```powershell
.\scripts\Start-Secure-Tunnel.ps1 -DoctorOnly
```

Also inspect `http://127.0.0.1:8080/ui`. The tunnel client must remain running for discovery and every later tool call.

