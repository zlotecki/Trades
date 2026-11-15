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
