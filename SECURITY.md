# Security policy

## Read this before use

ChatGPT Windows Portal intentionally exposes high-impact capabilities to an MCP client. Depending on the approved call, it can read or write files, execute shell commands, terminate processes, capture the desktop, control input, and launch programs with the same Windows privileges as the user who started it.

Treat access to the Portal as access to that Windows account.

## Safe defaults

This repository uses these defaults:

- The MCP listener binds only to `127.0.0.1`.
- DNS-rebinding protection is enabled.
- The recommended remote transport is OpenAI Secure MCP Tunnel, which makes an outbound HTTPS connection and does not require a public inbound MCP port.
- Machine-specific configuration, tunnel IDs, downloaded tools, screenshots, logs, and virtual environments are ignored by Git.
- The tunnel runtime API key is requested with hidden input and is not intentionally saved by the project.
- File writes, desktop control, process termination, program launches, and mutating shell commands include additional confirmation values.

Those controls reduce accidental misuse but do not make untrusted access safe.

## Required operating practices

1. Use the Portal only on a computer and account you are authorized to control.
2. Keep `PORTAL_BIND_HOST` set to `127.0.0.1` when using Secure MCP Tunnel.
3. Begin with ChatGPT's **Always ask** app permission.
4. Review exact paths, commands, coordinates, and target windows before approval.
5. Run the Portal as a standard Windows user, not Administrator, unless a specific task truly requires elevation.
6. Stop both Portal and tunnel terminals when remote access is not needed.
7. Revoke and replace a runtime API key that may have been exposed.
8. Keep Windows, Python packages, and `tunnel-client` updated.

## Do not expose the server directly

Do not forward port 8000 on a router, bind it to every interface, or publish a no-authentication ngrok/Cloudflare URL. The visible confirmation strings are tool-level interlocks; they are not user authentication.

If an organization cannot use Secure MCP Tunnel, place the server behind a professionally configured identity-aware gateway with TLS, strong authentication, authorization, rate limiting, and audit logging. A random hostname alone is not authentication.

## Secrets and personal data

Never commit or post:

- OpenAI, ngrok, or other access tokens;
- `config\secure-tunnel.env.ps1` or private profiles;
- screenshots or logs containing personal information;
- browser profiles, cookies, SSH keys, cloud credentials, or password-manager data;
- machine-specific public hostnames that are still active.

The `environment_variables` tool redacts variable names containing common secret terms, but no heuristic can catch every secret.

## Reporting a vulnerability

Do not open a public issue with exploit details or live credentials. Use GitHub's private vulnerability reporting feature if it is enabled for the repository. Include a minimal reproduction with all identities, keys, endpoints, paths, and personal data removed.

