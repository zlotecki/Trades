#!/bin/bash
# Build "AI Security.app" on a Mac.  Usage:  ./build_mac.sh
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet psutil pystray pillow pyinstaller
rm -rf build dist
pyinstaller --noconfirm AISecurity.spec
echo
echo "Built: $(pwd)/dist/AI Security.app"
echo "Try it:  open \"dist/AI Security.app\""
