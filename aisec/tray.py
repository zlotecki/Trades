"""System-tray icon + pop-up notifications. Falls back to the terminal if no GUI."""
from __future__ import annotations

import subprocess
import sys
import threading
from collections import deque

from . import autostart
from .cpu_monitor import stop_process


class AlertCenter:
    """Keeps recent alerts and builds the tray menu entries. GUI-free, testable."""

    def __init__(self, stopper=stop_process, keep: int = 10):
        self.recent: deque = deque(maxlen=keep)
        self.stopper = stopper
        self.last_result = ""

    def add(self, alert) -> str:
        self.recent.appendleft(alert)
        return alert.message

    def menu_entries(self) -> list[tuple[str, callable]]:
        return [(f"Stop {a.name} (PID {a.pid})", lambda a=a: self.stop(a))
                for a in self.recent]

    def stop(self, alert) -> bool:
        ok = self.stopper(alert.pid)
        self.last_result = (f"Stopped {alert.name}." if ok
                            else f"Could not stop {alert.name}.")
        if ok:
            self.recent = type(self.recent)((a for a in self.recent if a is not alert),
                                            maxlen=self.recent.maxlen)
        return ok


def _icon_image(color=(40, 160, 90)):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.polygon([(32, 4), (58, 14), (54, 40), (32, 60), (10, 40), (6, 14)], fill=color)
    return img


class Tray:
    error = ""
    """Wraps pystray. Use Tray.create() — returns None if no display is available."""

    def __init__(self, pystray, center: AlertCenter):
        self.pystray, self.center = pystray, center
        self.icon = pystray.Icon("aisec", _icon_image(), "AI Security: watching",
                                 menu=pystray.Menu(self._items))

    @classmethod
    def create(cls, center: AlertCenter):
        try:
            import pystray
            return cls(pystray, center)
        except Exception as e:  # no display / missing libs
            cls.error = f"{type(e).__name__}: {e}"
            return None

    def _items(self):
        P = self.pystray
        items = [P.MenuItem("AI Security is watching your computer", None, enabled=False)]
        for label, fn in self.center.menu_entries():
            items.append(P.MenuItem(label, self._make_stop(fn)))
        if self.center.recent:
            items.append(P.MenuItem("Dismiss all warnings", self._dismiss))
        items.append(P.MenuItem("Start at login", self._toggle_login,
                                checked=lambda item: autostart.target().exists()))
        items.append(P.MenuItem("Quit", lambda icon, item: icon.stop()))
        return items

    def _toggle_login(self, icon, item):
        if autostart.target().exists():
            autostart.uninstall()
        else:
            autostart.install()
        self.icon.update_menu()

    def _dismiss(self, icon, item):
        self.center.recent.clear()
        self._refresh()

    def _refresh(self):
        """Green when no warnings are open, red otherwise. Main thread only."""
        ok = not self.center.recent
        self.icon.icon = _icon_image((40, 160, 90) if ok else (200, 40, 40))
        self.icon.title = "AI Security: watching" if ok else "AI Security: WARNING"
        self.icon.update_menu()

    def _make_stop(self, fn):
        # pystray allows at most 2 positional args, so bind fn via a closure.
        def action(icon, item):
            self._stop(fn)
        return action

    def _stop(self, fn):
        fn()
        if sys.platform == "darwin":
            self._mac_popup(self.center.last_result)
        else:
            self.icon.notify(self.center.last_result)
        self._refresh()

    @staticmethod
    def _on_main(fn) -> None:
        """macOS only allows menu-bar changes on the main thread."""
        if sys.platform == "darwin":
            from PyObjCTools import AppHelper
            AppHelper.callAfter(fn)
        else:
            fn()

    def _mac_popup(self, text: str) -> None:
        esc = text.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.run(["osascript", "-e",
                        f'display notification "{esc}" with title "AI Security warning" '
                        'sound name "Basso"'], check=False, timeout=10)

    def notify(self, alert) -> None:
        """Safe to call from any thread."""
        self.center.add(alert)

        def update():
            self._refresh()
            if sys.platform != "darwin":
                self.icon.notify(alert.message, "⚠️ AI Security warning")

        self._on_main(update)
        if sys.platform == "darwin":
            self._mac_popup(alert.message)  # thread-safe, works on new macOS

    def run(self, worker) -> None:
        """Run the tray on the main thread, `worker(notify)` on a background thread."""
        def setup(icon):
            icon.visible = True
            threading.Thread(target=worker, args=(self.notify,), daemon=True).start()
        self.icon.run(setup)
