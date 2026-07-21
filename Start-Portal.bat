@echo off
setlocal
title ChatGPT Windows Portal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-Portal.ps1"
if errorlevel 1 pause

