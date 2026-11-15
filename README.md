# AI Security (prototype)

Background watcher that warns beginners when code they ran misbehaves:
CPU miners, access to browser passwords/cookies/API keys, and scripts
connecting to unfamiliar servers.

    pip install -r requirements.txt
    python -m aisec.main            # system-tray icon + pop-ups
    python -m aisec.main --no-tray  # terminal alerts
    python -m pytest

Mac: grant Full Disk Access to your terminal/Python for full visibility.
