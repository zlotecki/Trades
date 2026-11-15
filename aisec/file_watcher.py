"""Flag programs that open browser password/cookie files or API-key files."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import psutil

HOME = Path.home()


def sensitive_paths() -> dict[str, set[str]]:
    """Map of sensitive file path -> names of processes allowed to open it."""
    chrome = {"chrome", "chrome.exe", "google chrome", "google chrome helper"}
    edge = {"msedge.exe", "microsoft edge", "microsoft edge helper"}
    firefox = {"firefox", "firefox.exe"}
    safari = {"safari", "com.apple.safari.safebrowsing"}
    out: dict[str, set[str]] = {}

    def add(path: Path, owners: set[str]) -> None:
        out[str(path)] = owners

    if sys.platform == "win32":
        local = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData/Local"))
        roam = Path(os.environ.get("APPDATA", HOME / "AppData/Roaming"))
        for base, owners in ((local / "Google/Chrome/User Data/Default", chrome),
                             (local / "Microsoft/Edge/User Data/Default", edge)):
            add(base / "Login Data", owners)
            add(base / "Network/Cookies", owners)
        ff = roam / "Mozilla/Firefox/Profiles"
        if ff.exists():
            for prof in ff.iterdir():
                for f in ("logins.json", "key4.db", "cookies.sqlite"):
                    add(prof / f, firefox)
    elif sys.platform == "darwin":
        lib = HOME / "Library"
        for base, owners in ((lib / "Application Support/Google/Chrome/Default", chrome),
                             (lib / "Application Support/Microsoft Edge/Default", edge)):
            add(base / "Login Data", owners)
            add(base / "Cookies", owners)
        ff = lib / "Application Support/Firefox/Profiles"
        if ff.exists():
            for prof in ff.iterdir():
                for f in ("logins.json", "key4.db", "cookies.sqlite"):
                    add(prof / f, firefox)
        add(lib / "Cookies/Cookies.binarycookies", safari)
    else:  # Linux (also handy for testing)
        for base, owners in ((HOME / ".config/google-chrome/Default", chrome),
                             (HOME / ".config/microsoft-edge/Default", edge)):
            add(base / "Login Data", owners)
            add(base / "Cookies", owners)
        ff = HOME / ".mozilla/firefox"
        if ff.exists():
            for prof in ff.iterdir():
                for f in ("logins.json", "key4.db", "cookies.sqlite"):
                    add(prof / f, firefox)
    # API keys / tokens: no process is expected to hold these open.
    for f in (".env", ".aws/credentials", ".config/openai/api_key",
              ".anthropic/api_key", ".ssh/id_rsa", ".ssh/id_ed25519"):
        add(HOME / f, set())
    return out


@dataclass
class Access:
    pid: int
    name: str
    path: str
    message: str


@dataclass
class FileWatcher:
    watched: dict = field(default_factory=sensitive_paths)
    _seen: set = field(default_factory=set)

    def evaluate(self, open_files: dict, now=None) -> list[Access]:
        """open_files: pid -> (process name, [paths]). Pure logic for testing."""
        alerts = []
        for pid, (name, paths) in open_files.items():
            for path in paths:
                owners = self.watched.get(path)
                if owners is None or name.lower() in owners:
                    continue
                if (pid, path) in self._seen:
                    continue
                self._seen.add((pid, path))
                kind = "saved passwords/logins" if "Login" in path or "logins" in path \
                    else "login cookies" if "ookie" in path else "secret keys"
                alerts.append(Access(pid, name, path, (
                    f"'{name}' (PID {pid}) opened a file holding your {kind}: {path}. "
                    "Only your browser should do that. If you just ran code from "
                    "someone else, stop it.")))
        return alerts

    def sample(self) -> dict:
        out = {}
        for p in psutil.process_iter(["pid", "name"]):
            try:
                files = [f.path for f in p.open_files()]
            except (psutil.Error, OSError):
                continue  # needs elevated permission for some processes
            hits = [f for f in files if f in self.watched]
            if hits:
                out[p.info["pid"]] = (p.info["name"] or "?", hits)
        return out

    def poll(self) -> list[Access]:
        return self.evaluate(self.sample())
