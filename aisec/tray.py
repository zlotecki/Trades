"""System-tray icon + pop-up notifications. Falls back to the terminal if no GUI."""
from __future__ import annotations

import threading
from collections import deque

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
        except Exception:  # no display / missing libs
            return None

    def _items(self):
        P = self.pystray
        items = [P.MenuItem("AI Security is watching your computer", None, enabled=False)]
        for label, fn in self.center.menu_entries():
            items.append(P.MenuItem(label, lambda icon, item, fn=fn: self._stop(fn)))
        items.append(P.MenuItem("Quit", lambda icon, item: icon.stop()))
        return items

    def _stop(self, fn):
        fn()
        self.icon.notify(self.center.last_result)
        self.icon.update_menu()

    def notify(self, alert) -> None:
        self.center.add(alert)
        self.icon.icon = _icon_image((200, 40, 40))
        self.icon.title = "AI Security: WARNING"
        self.icon.notify(alert.message, "⚠️ AI Security warning")
        self.icon.update_menu()

    def run(self, worker) -> None:
        """Run the tray on the main thread, `worker(notify)` on a background thread."""
        def setup(icon):
            icon.visible = True
            threading.Thread(target=worker, args=(self.notify,), daemon=True).start()
        self.icon.run(setup)
