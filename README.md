# PAC Proxy Server — tray app

Serves `proxy.pac` from `pac_server.py`, wrapped in a Windows system-tray app.

## Prerequisites

Before building the executable, ensure you have the following installed:

- **Python 3.12+**: Required for running the scripts and building the app.
- **Node.js & npm**: Required by some dependencies or for specific build steps (if applicable).
- **PyInstaller**: Used to bundle the application into an `.exe`.

## Run the exe

`dist\PACProxyTray.exe` (keep `config.json` in the same folder as the exe).

- A tray icon appears; right-click for:
  - **Open PAC file** / **Open status page** (double-click the icon opens the PAC file)
  - **Open config folder**
  - **Quit** — stops the server and removes the icon
- Only one instance runs at a time; launching again shows a message instead of a second icon.
- Port defaults to `8080` (override with the `PAC_SERVER_PORT` environment variable).

## Rebuild

```bat
build.bat
```

The script creates `.venv` if needed, installs `requirements.txt`, regenerates `icon.ico`,
and writes `dist\PACProxyTray.exe` plus a copy of `config.json`.

## Files

- `pac_server.py` — PAC generation and HTTP server (unchanged)
- `tray_app.py` — tray icon, menu, background server thread, single-instance guard
- `make_icon.py` — generates `icon.ico` for the exe
- `config.json` — proxy rules, read from next to the exe when frozen