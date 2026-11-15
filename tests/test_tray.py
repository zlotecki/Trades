from types import SimpleNamespace as A

from aisec.tray import AlertCenter, Tray


def test_menu_and_stop():
    stopped = []
    c = AlertCenter(stopper=lambda pid: stopped.append(pid) or True)
    c.add(A(pid=7, name="miner", message="m"))
    (label, fn), = c.menu_entries()
    assert label == "Stop miner (PID 7)"
    fn()
    assert stopped == [7] and not c.recent and "Stopped" in c.last_result


def test_failed_stop_keeps_alert():
    c = AlertCenter(stopper=lambda pid: False)
    c.add(A(pid=1, name="x", message="m"))
    c.menu_entries()[0][1]()
    assert len(c.recent) == 1 and "Could not" in c.last_result


def test_no_display_falls_back():
    assert Tray.create(AlertCenter()) is None  # headless CI


def test_menu_actions_accepted_by_pystray():
    # Regression: pystray rejects callbacks with more than 2 positional args.
    import pytest
    try:
        import pystray
    except Exception:
        pytest.skip("no display")
    t = Tray.__new__(Tray)
    t.pystray, t.center = pystray, AlertCenter()
    t.icon = type("I", (), {})()
    action = t._make_stop(lambda: None)
    pystray.MenuItem("x", action)  # raises ValueError if invalid


def test_shield_returns_to_green_after_stop_and_dismiss():
    class FakeIcon:
        icon = None
        title = ""
        def update_menu(self): pass
        def notify(self, *a): pass

    t = Tray.__new__(Tray)
    t.center = AlertCenter(stopper=lambda pid: True)
    t.icon = FakeIcon()
    t.center.add(A(pid=1, name="x", message="m"))
    t._refresh()
    assert t.icon.title.endswith("WARNING")
    t._stop(t.center.menu_entries()[0][1])
    assert t.icon.title.endswith("watching")
    t.center.add(A(pid=2, name="y", message="m"))
    t._refresh()
    t._dismiss(None, None)
    assert t.icon.title.endswith("watching")
