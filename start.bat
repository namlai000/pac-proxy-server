@echo off
title PAC Proxy Server
echo Starting PAC Proxy Server (port 8000)...
:retry
python "%~dp0pac_server.py"
if errorlevel 1 (
	echo PAC Proxy Server crashed. Restarting in 5 seconds...
	timeout /t 5 /nobreak >nul
	goto retry
)
pause
