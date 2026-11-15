"""Flag scripts (Python, Node, ...) connecting to unfamiliar servers."""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field

import psutil

SCRIPT_RUNNERS = ("python", "node", "deno", "bun", "powershell", "pwsh", "wscript",
                  "cscript", "bash", "sh", "zsh", "perl", "ruby", "java")
# Servers beginners' scripts normally talk to. Matched against the host name.
TRUSTED_DOMAINS = (
    "anthropic.com", "openai.com", "github.com", "githubusercontent.com",
    "pypi.org", "pythonhosted.org", "npmjs.org", "npmjs.com", "googleapis.com",
    "google.com", "microsoft.com", "amazonaws.com", "cloudflare.com",
)


def is_script_runner(name: str) -> bool:
    n = name.lower().removesuffix(".exe")
    return any(n == r or n.startswith(r) for r in SCRIPT_RUNNERS)


def is_public(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def is_trusted_host(host: str | None) -> bool:
    return bool(host) and any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


def reverse_dns(ip: str) -> str | None:
    try:
        socket.setdefaulttimeout(1.0)
        return socket.gethostbyaddr(ip)[0].lower()
    except (OSError, socket.herror):
        return None


@dataclass
class Connection:
    pid: int
    name: str
    ip: str
    port: int
    host: str | None
    message: str


@dataclass
class NetWatcher:
    resolver: callable = reverse_dns
    _seen: set = field(default_factory=set)

    def evaluate(self, conns: list) -> list[Connection]:
        """conns: list of (pid, process name, remote ip, remote port)."""
        alerts = []
        for pid, name, ip, port in conns:
            if not is_script_runner(name) or not is_public(ip) or (pid, ip) in self._seen:
                continue
            self._seen.add((pid, ip))
            host = self.resolver(ip)
            if is_trusted_host(host):
                continue
            where = f"{host} ({ip})" if host else ip
            alerts.append(Connection(pid, name, ip, port, host, (
                f"'{name}' (PID {pid}) is sending data to an unfamiliar server: "
                f"{where}:{port}. Scripts that secretly upload your files do this. "
                "If you don't know why, stop it.")))
        return alerts

    def sample(self) -> list:
        out = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                for c in p.net_connections(kind="inet"):
                    if c.raddr and c.status == psutil.CONN_ESTABLISHED:
                        out.append((p.info["pid"], p.info["name"] or "?", c.raddr.ip, c.raddr.port))
            except (psutil.Error, OSError):
                continue
        return out

    def poll(self) -> list[Connection]:
        return self.evaluate(self.sample())
