from aisec.cpu_monitor import CpuMonitor


def test_alerts_after_sustained_load():
    m = CpuMonitor(threshold=80, sustain_seconds=60)
    assert m.evaluate({1: ("miner", 95)}, 0) == []
    assert m.evaluate({1: ("miner", 95)}, 30) == []
    a = m.evaluate({1: ("miner", 95)}, 61)
    assert len(a) == 1 and a[0].pid == 1
    assert m.evaluate({1: ("miner", 95)}, 90) == []  # no repeat


def test_dip_resets_timer():
    m = CpuMonitor(threshold=80, sustain_seconds=60)
    m.evaluate({1: ("x", 95)}, 0)
    m.evaluate({1: ("x", 5)}, 40)
    assert m.evaluate({1: ("x", 95)}, 70) == []


def test_allowlist_ignored():
    m = CpuMonitor(threshold=80, sustain_seconds=10)
    m.evaluate({1: ("chrome.exe", 99)}, 0)
    assert m.evaluate({1: ("chrome.exe", 99)}, 20) == []
