"""System-tray launcher for the PAC proxy server.

Runs pac_server in a background thread and exposes it through a tray icon.
Right-click the icon for options (open PAC URL, status page, config folder, quit).
"""

import ctypes
import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

import pac_server

APP_NAME = "PAC Proxy Server"
MUTEX_NAME = "Local\\PACProxyTraySingleton"
ERROR_ALREADY_EXISTS = 183
MB_ICONERROR = 0x00000010
MB_ICONINFORMATION = 0x00000040

PAC_URL = f"http://localhost:{pac_server.PAC_SERVER_PORT}/proxy.pac"
STATUS_URL = f"http://localhost:{pac_server.PAC_SERVER_PORT}/status"

# Keep a reference so the mutex handle is not garbage collected.
_mutex_handle = None


def base_dir() -> Path:
    """Directory of the exe when frozen, otherwise the script directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def build_icon(size: int = 64) -> Image.Image:
    """Draw the tray icon (a PAC-man style wedge) so no external asset is needed."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    draw.pieslice(
        (pad, pad, size - pad, size - pad),
        start=35,
        end=325,
        fill=(255, 187, 0, 255),
        outline=(140, 85, 0, 255),
        width=max(1, size // 32),
    )
    # Eye
    eye = max(2, size // 10)
    cx, cy = int(size * 0.52), int(size * 0.28)
    draw.ellipse((cx - eye, cy - eye, cx + eye, cy + eye), fill=(60, 40, 0, 255))
    return img


class ProxyService:
    """Owns the HTTP server and its worker thread."""

    def __init__(self) -> None:
        self.server = None
        self.thread = None
        self.error = None

    def start(self) -> bool:
        try:
            self.server = pac_server.ThreadingHTTPServer(
                ("0.0.0.0", pac_server.PAC_SERVER_PORT), pac_server.PACHandler
            )
        except OSError as exc:
            self.error = exc
            return False

        self.thread = threading.Thread(
            target=self.server.serve_forever, name="pac-server", daemon=True
        )
        self.thread.start()
        return True

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread is not None:
            self.thread.join(timeout=5)
            self.thread = None


def open_config_folder() -> None:
    config_file = Path(pac_server.CONFIG_FILE)
    try:
        if config_file.exists():
            subprocess.Popen(["explorer", "/select,", str(config_file)])
        else:
            os.startfile(str(base_dir()))
    except OSError:
        pass


def build_menu(service: ProxyService) -> pystray.Menu:
    return pystray.Menu(
        pystray.MenuItem("Open PAC file", lambda: webbrowser.open(PAC_URL), default=True),
        pystray.MenuItem("Open status page", lambda: webbrowser.open(STATUS_URL)),
        pystray.MenuItem("Open config folder", lambda: open_config_folder()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            f"Proxy target: {pac_server.PROXY_HOST}:{pac_server.PROXY_PORT}",
            None,
            enabled=False,
        ),
        pystray.MenuItem(f"Rules loaded: {len(pac_server.PROXY_RULES)}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda icon, item: icon.stop()),
    )


def acquire_single_instance_mutex():
    """Return a mutex handle, or None if another instance already owns it."""
    global _mutex_handle
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        _mutex_handle = None
        return None
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        _mutex_handle = None
        return None
    _mutex_handle = handle
    return handle


def message_box(text: str, flags: int) -> None:
    ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, flags)


def redirect_std_streams() -> None:
    """A windowed exe has no console; keep stray prints from failing."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main() -> int:
    redirect_std_streams()

    if acquire_single_instance_mutex() is None:
        message_box(
            f"{APP_NAME} is already running.\n"
            "Look for its icon in the notification area.",
            MB_ICONINFORMATION,
        )
        return 0

    service = ProxyService()
    if not service.start():
        message_box(
            f"Could not start the server on port {pac_server.PAC_SERVER_PORT}.\n\n"
            f"{service.error}\n\n"
            "Another program may be using that port. You can change it with the "
            "PAC_SERVER_PORT environment variable.",
            MB_ICONERROR,
        )
        return 1

    icon = pystray.Icon("pac-proxy", build_icon(), APP_NAME, menu=build_menu(service))

    def on_ready(icon: pystray.Icon) -> None:
        icon.visible = True
        try:
            icon.notify(f"Running at {PAC_URL}", APP_NAME)
        except Exception:
            pass

    try:
        icon.run(setup=on_ready)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
