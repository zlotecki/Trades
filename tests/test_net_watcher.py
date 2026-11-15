from aisec.net_watcher import NetWatcher, is_script_runner


def w(host=None):
    return NetWatcher(resolver=lambda ip: host)


def test_unknown_server_flagged_once():
    n = w()
    c = [(1, "python3", "8.8.8.8", 443)]
    assert len(n.evaluate(c)) == 1
    assert n.evaluate(c) == []


def test_trusted_host_ignored():
    assert w("api.anthropic.com").evaluate([(1, "node", "8.8.8.8", 443)]) == []


def test_local_and_private_ignored():
    n = w()
    assert n.evaluate([(1, "python3", "127.0.0.1", 80), (1, "python3", "192.168.1.5", 80)]) == []


def test_non_script_ignored():
    assert w().evaluate([(1, "chrome.exe", "8.8.8.8", 443)]) == []


def test_runner_names():
    assert is_script_runner("python3.12") and is_script_runner("node.exe")
    assert not is_script_runner("chrome")
