# Contributing

Contributions are welcome, especially improvements to Windows compatibility, tool annotations, tests, accessibility, and safe configuration.

## Local validation

On Windows:

```powershell
.\Install-Portal.bat
.\scripts\Test-Portal.ps1
```

Before submitting a change:

- preserve the loopback-only default;
- do not weaken confirmation checks;
- do not commit credentials, active endpoints, logs, screenshots, browser data, or machine-specific paths;
- update `docs/TOOLS.md` when tools change;
- test with a standard Windows user account;
- explain any new mutating capability clearly.

By contributing, you agree that your contribution is licensed under the project's MIT License.

