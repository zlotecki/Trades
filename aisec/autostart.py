"""Start AI Security automatically at login (Windows, Mac, Linux)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def command() -> list[str]:
    exe = sys.executable
    if sys.platform == "win32":  # pythonw has no console window
        exe = exe.replace("python.exe", "pythonw.exe")
    return [exe, "-m", "aisec.main"]


def project_dir() -> str:
    """Folder that contains the aisec package, so `-m aisec.main` is importable."""
    return str(Path(__file__).resolve().parent.parent)


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
        return f'@echo off\r\ncd /d "{project_dir()}"\r\nstart "" ' + " ".join(f'"{c}"' for c in cmd) + "\r\n"
    if platform == "darwin":
        args = "".join(f"    <string>{c}</string>\n" for c in cmd)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<plist version="1.0"><dict>\n'
                '  <key>Label</key><string>com.aisecurity.app</string>\n'
                f'  <key>ProgramArguments</key><array>\n{args}  </array>\n'
                f'  <key>WorkingDirectory</key><string>{project_dir()}</string>\n'
                '  <key>RunAtLoad</key><true/>\n'
                '  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>\n'
                '</dict></plist>\n')
    return ("[Desktop Entry]\nType=Application\nName=AI Security\n"
            f"Path={project_dir()}\nExec={' '.join(cmd)}\nX-GNOME-Autostart-enabled=true\n")


def install(**kw) -> Path:
    path = target(**{k: v for k, v in kw.items() if k in ("platform", "home")})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(kw.get("platform", sys.platform)))
    if kw.get("platform", sys.platform) == "darwin" and "home" not in kw:
        subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        subprocess.run(["launchctl", "load", "-w", str(path)], check=False)  # start now
    return path


def uninstall(**kw) -> bool:
    path = target(**{k: v for k, v in kw.items() if k in ("platform", "home")})
    if path.exists():
        if kw.get("platform", sys.platform) == "darwin" and "home" not in kw:
            subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        path.unlink()
        return True
    return False
