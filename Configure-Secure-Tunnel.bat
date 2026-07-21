@echo off
setlocal
title Configure OpenAI Secure MCP Tunnel
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Configure-Secure-Tunnel.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" echo Tunnel setup failed with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

