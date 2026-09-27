#!/bin/bash
# Move to directory where this script is located
cd "$(dirname "$0")"

echo "================================================="
echo "   CGSUSA Materials Manual Downloader (macOS)"
echo "================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Error: python3 could not be found."
    echo "    Please install Python from https://www.python.org/downloads/macos/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Set up virtual environment if needed
if [ ! -d "venv" ]; then
    echo "[*] Setting up local environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet -r requirements.txt

# Run downloader with any passed arguments or default all
python3 download_manuals.py "$@"

echo ""
read -p "Press Enter to exit..."
