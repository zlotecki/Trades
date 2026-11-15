"""CPU spike check: flag unknown processes that keep the CPU busy for a long time."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import psutil

# Processes we trust to be busy (browsers, compilers, system). Extend as needed.
DEFAULT_ALLOWLIST = {
    "system", "system idle process", "kernel_task", "windowserver", "svchost.exe",
    "chrome", "chrome.exe", "msedge.exe", "firefox", "firefox.exe", "safari",
    "code", "code.exe", "zoom.us", "teams.exe",
}


def _fmt(sec: float) -> str:
    return f"{int(sec // 60)} min" if sec >= 60 else f"{int(sec)} sec"


@dataclass
class Alert:
    pid: int
    name: str
    cpu_percent: float
    seconds: float
    message: str


@dataclass
class CpuMonitor:
    threshold: float = 80.0        # % of one core considered "heavy"
    sustain_seconds: float = 60.0  # how long it must stay heavy before alerting
    allowlist: set = field(default_factory=lambda: set(DEFAULT_ALLOWLIST))
    _since: dict = field(default_factory=dict)    # pid -> time heavy usage began
    _alerted: set = field(default_factory=set)    # pids already alerted

    def evaluate(self, samples: dict, now: float) -> list[Alert]:
        """samples: pid -> (name, cpu_percent). Pure logic, easy to test."""
        alerts = []
        for pid in list(self._since):
            if pid not in samples or samples[pid][1] < self.threshold:
                self._since.pop(pid)
                self._alerted.discard(pid)
        for pid, (name, cpu) in samples.items():
            if name.lower() in self.allowlist or cpu < self.threshold:
                continue
            start = self._since.setdefault(pid, now)
            held = now - start
            if held >= self.sustain_seconds and pid not in self._alerted:
                self._alerted.add(pid)
                alerts.append(Alert(pid, name, cpu, held, (
                    f"'{name}' (PID {pid}) has been using {cpu:.0f}% CPU for "
                    f"{_fmt(held)}. Hidden crypto miners behave like this. "
                    "If you don't recognise it, stop it.")))
        return alerts

    def sample(self) -> dict:
        out = {}
        for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                out[p.info["pid"]] = (p.info["name"] or "?", p.info["cpu_percent"] or 0.0)
            except psutil.Error:
                continue
        return out

    def poll(self) -> list[Alert]:
        return self.evaluate(self.sample(), time.monotonic())


def stop_process(pid: int) -> bool:
    try:
        psutil.Process(pid).terminate()
        return True
    except psutil.Error:
        return False
