"""Run the CPU spike check in the foreground. Ctrl+C to quit."""
import argparse
import time

import psutil

from .cpu_monitor import CpuMonitor, stop_process


def notify(alert) -> None:
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
    a = ap.parse_args()
    mon = CpuMonitor(a.threshold, a.sustain)
    psutil.cpu_percent(None)
    mon.sample()  # prime per-process counters
    print("AI Security watching CPU... (Ctrl+C to quit)")
    while True:
        time.sleep(a.interval)
        for alert in mon.poll():
            notify(alert)


if __name__ == "__main__":
    main()
