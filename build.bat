@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
	echo Creating virtual environment...
	python -m venv .venv
	if errorlevel 1 goto :error
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Generating icon...
".venv\Scripts\python.exe" make_icon.py
if errorlevel 1 goto :error

echo Building exe...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed ^
	--name "PACProxyTray" --icon icon.ico ^
	--hidden-import pystray._win32 ^
	tray_app.py
if errorlevel 1 goto :error

echo Copying config.json next to the exe...
copy /y "config.json" "dist\config.json" >nul

echo.
echo Done: %~dp0dist\PACProxyTray.exe
exit /b 0

:error
echo.
echo Build failed.
exit /b 1
