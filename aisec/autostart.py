"""Start AI Security automatically at login (Windows, Mac, Linux)."""
from __future__ import annotations

import sys
from pathlib import Path


def command() -> list[str]:
    exe = sys.executable
    if sys.platform == "win32":  # pythonw has no console window
        exe = exe.replace("python.exe", "pythonw.exe")
    return [exe, "-m", "aisec.main"]


def target(platform: str = sys.platform, home: Path | None = None) -> Path:
    home = home or Path.home()
    if platform == "win32":
        return home / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/AISecurity.bat"
    if platform == "darwin":
        return home / "Library/LaunchAgents/com.aisecurity.app.plist"
    return home / ".config/autostart/aisecurity.desktop"


def render(platform: str = sys.platform, cmd: list[str] | None = None) -> str:
    cmd = cmd or command()
    if platform == "win32":
        return "@echo off\r\nstart \"\" " + " ".join(f'"{c}"' for c in cmd) + "\r\n"
    if platform == "darwin":
        args = "".join(f"    <string>{c}</string>\n" for c in cmd)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<plist version="1.0"><dict>\n'
                '  <key>Label</key><string>com.aisecurity.app</string>\n'
                f'  <key>ProgramArguments</key><array>\n{args}  </array>\n'
                '  <key>RunAtLoad</key><true/>\n  <key>KeepAlive</key><true/>\n'
                '</dict></plist>\n')
    return ("[Desktop Entry]\nType=Application\nName=AI Security\n"
            f"Exec={' '.join(cmd)}\nX-GNOME-Autostart-enabled=true\n")


def install(**kw) -> Path:
    path = target(**{k: v for k, v in kw.items() if k in ("platform", "home")})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(kw.get("platform", sys.platform)))
    return path


def uninstall(**kw) -> bool:
    path = target(**{k: v for k, v in kw.items() if k in ("platform", "home")})
    if path.exists():
        path.unlink()
        return True
    return False
