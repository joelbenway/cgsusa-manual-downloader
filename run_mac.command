#!/bin/bash
# Copyright (c) 2026  Joel Benway
# SPDX-License-Identifier: AGPL-3.0-or-later
# Please see end of file for extended copyright information

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

# This file is part of cgsusa-manual-downloader.
#
# cgsusa-manual-downloader is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# cgsusa-manual-downloader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
# more details.
#
# You should have received a copy of the GNU Affero General Public License along with
# cgsusa-manual-downloader. If not, see <https://www.gnu.org/licenses/>.
