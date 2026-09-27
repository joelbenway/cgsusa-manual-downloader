#!/bin/bash
# Builds a standalone macOS executable using PyInstaller
cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --name "cgsusa_manual_downloader" download_manuals.py

echo ""
echo "[+] Build complete! Standalone macOS binary is located in: dist/cgsusa_manual_downloader"
