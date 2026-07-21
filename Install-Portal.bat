@echo off
setlocal
title Install ChatGPT Windows Portal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Setup-Portal.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" echo Installation failed with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

