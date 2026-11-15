from aisec.file_watcher import FileWatcher

W = {"/h/Login Data": {"chrome"}, "/h/.env": set()}


def test_owner_is_ignored():
    assert FileWatcher(W).evaluate({1: ("chrome", ["/h/Login Data"])}) == []


def test_other_process_flagged_once():
    w = FileWatcher(W)
    a = w.evaluate({2: ("python3", ["/h/Login Data"])})
    assert len(a) == 1 and "python3" in a[0].message
    assert w.evaluate({2: ("python3", ["/h/Login Data"])}) == []


def test_env_file_flagged_for_anyone():
    assert len(FileWatcher(W).evaluate({3: ("node", ["/h/.env"])})) == 1
