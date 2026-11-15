from pathlib import Path

from aisec import autostart

CMD = ["/usr/bin/python3", "-m", "aisec.main"]


def test_render_each_platform():
    assert "RunAtLoad" in autostart.render("darwin", CMD)
    assert "Exec=/usr/bin/python3 -m aisec.main" in autostart.render("linux", CMD)
    assert autostart.render("win32", CMD).startswith("@echo off")


def test_install_uninstall(tmp_path: Path):
    p = autostart.install(platform="linux", home=tmp_path)
    assert p.exists() and p.parent.name == "autostart"
    assert autostart.uninstall(platform="linux", home=tmp_path)
    assert not p.exists() and not autostart.uninstall(platform="linux", home=tmp_path)


def test_targets():
    h = Path("/h")
    assert "LaunchAgents" in str(autostart.target("darwin", h))
    assert "Startup" in str(autostart.target("win32", h))
