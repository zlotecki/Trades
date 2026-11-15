"""Run all checks in the background with a tray icon (or terminal fallback)."""
import argparse
import time

import psutil

from . import autostart
from .cpu_monitor import CpuMonitor, stop_process
from .file_watcher import FileWatcher
from .net_watcher import NetWatcher
from .tray import AlertCenter, Tray


def console_notify(alert) -> None:
    print(f"\n⚠️  WARNING: {alert.message}")
    try:
        if input("Stop this process? [y/N] ").strip().lower() == "y":
            print("Stopped." if stop_process(alert.pid) else "Could not stop it.")
    except EOFError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=80.0)
    ap.add_argument("--sustain", type=float, default=60.0, help="seconds")
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--no-tray", action="store_true", help="print alerts in the terminal")
    ap.add_argument("--install", action="store_true", help="start automatically at login")
    ap.add_argument("--uninstall", action="store_true", help="stop starting at login")
    a = ap.parse_args()
    if a.install:
        print("Will start at login:", autostart.install())
        return
    if a.uninstall:
        print("Removed autostart." if autostart.uninstall() else "Autostart was not set.")
        return
    mon, fw, nw = CpuMonitor(a.threshold, a.sustain), FileWatcher(), NetWatcher()
    mon.sample()  # prime per-process CPU counters

    def watch(notify):
        while True:
            time.sleep(a.interval)
            for alert in mon.poll() + fw.poll() + nw.poll():
                notify(alert)

    tray = None if a.no_tray else Tray.create(AlertCenter())
    if tray:
        print("AI Security running in the system tray.")
        tray.run(watch)
    else:
        print("AI Security watching CPU, files and connections... (Ctrl+C to quit)")
        try:
            watch(console_notify)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
