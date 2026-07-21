@echo off
setlocal
title ChatGPT Windows Portal and Secure Tunnel
if not exist "%~dp0config\secure-tunnel.env.ps1" (
  echo Secure Tunnel is not configured yet.
  echo Run Configure-Secure-Tunnel.bat first.
  pause
  exit /b 1
)
start "ChatGPT Windows Portal" cmd.exe /k ""%~dp0Start-Portal.bat""
timeout /t 3 /nobreak >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-Secure-Tunnel.ps1"
if errorlevel 1 pause

