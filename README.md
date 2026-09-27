# CGSUSA Materials Manual Downloader

Automates downloading and organizing all Catechesis of the Good Shepherd (CGSUSA) Materials Manual PDFs into structured folders ready for printing.

---

## 🚀 Quick Start (No Python or Technical Setup Required!)

You do not need to install Python or know how to code. Just download the ready-to-run app for your computer:

| Operating System | Download | Instructions |
|---|---|---|
| **Windows** | [**Download for Windows (.exe)**](https://github.com/joelbenway/cgsusa-manual-downloader/releases/latest) | Download `cgsusa_manual_downloader.exe` and **double-click** it. |
| **macOS** | [**Download for Mac**](https://github.com/joelbenway/cgsusa-manual-downloader/releases/latest) | Download `cgsusa_manual_downloader-macos`, open Terminal in that folder, and run: <br>`chmod +x ./cgsusa_manual_downloader-macos && ./cgsusa_manual_downloader-macos` |

*(A precompiled Windows `.exe` is also included directly in this repository: [cgsusa_manual_downloader.exe](cgsusa_manual_downloader.exe).)*

### How It Works:
1. **Launch the app** (double-click on Windows, or run in Terminal on Mac).
2. **Enter your CGSUSA member email and password** when prompted (password typing is hidden for privacy).
3. The app automatically downloads and organizes all **Level 1, Level 2, and Level 3** manuals into labelled folders next to the program:

```text
📁 level 1/
   📁 Incarnation Geography of Israel/
      📁 Globe and Raised Surface Map of Israel/
         📄 1-Directions_for_Israel_Raised-Surface-Wall...pdf
         📄 1-GEO_Raised_Surface_Model_DIR_2014.pdf
         📄 Raised_Surface_Collage_PIeces___Symbols2.pdf
      📁 Puzzle Map of Israel/
         📄 1-Regions_Puzzle_DIRECTIONS_2014-1.pdf
   📁 Baptism/
   📁 Eucharist/
   📁 Kingdom of God Parables/
   📁 Liturgical Calendar/
   ...
📁 level 2/
📁 level 3/
```

- **Safe to re-run anytime**: Already-downloaded files are automatically recognized and skipped.
- **Remembers your login**: Securely caches your session token locally (`cgsusa_session.json`) so you don't need to re-enter your password on future runs.
- **Connection resilient**: Automatically recovers and retries if the server drops a connection during download.

---

## Optional: Command Line Options

If you run the app from PowerShell, Command Prompt, or Terminal, you can customize what it does:

| Flag | Description |
|---|---|
| *(no arguments)* | Automatically downloads **all levels** (Level 1, 2, and 3) |
| `--level 1` / `2` / `3` / `all` | Download a specific level or all (default: `all`) |
| `--version` | Display program version |
| `--help` | Display help and usage details |
| `--outdir <path>` | Specify custom output folder |
| `--no-cache` | Force a new login instead of using cached session |
| `--no-pause` | Don't pause for Enter before exiting |

### Examples (Windows):
```powershell
# Download all levels (default)
.\cgsusa_manual_downloader.exe

# Download only Level 1
.\cgsusa_manual_downloader.exe --level 1

# Check version
.\cgsusa_manual_downloader.exe --version
```

### Examples (macOS):
```bash
# Download all levels (default)
./cgsusa_manual_downloader-macos

# Download only Level 2
./cgsusa_manual_downloader-macos --level 2
```

---

## 🛠️ Advanced: Running from Source / Building Locally (Developers)

If you want to inspect or modify the source code, run with Python directly, or compile binaries manually:

### 1. Running with Python Directly

#### Windows:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python download_manuals.py
```
*(You can also use the shorthand wrapper: `.\download_manuals`)*

#### macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 download_manuals.py
```
*(Mac users can also double-click [run_mac.command](run_mac.command).)*

---

### 2. Building Standalone Binaries Locally

- **Windows (.exe)**:
  ```powershell
  pip install pyinstaller
  pyinstaller --noconfirm --onefile --console --name "cgsusa_manual_downloader" download_manuals.py
  ```

- **macOS Binary**:
  ```bash
  bash build_mac.sh
  ```

- **Automated Cloud Builds (GitHub CI)**:
  A GitHub Actions workflow is included at [.github/workflows/ci.yaml](.github/workflows/ci.yaml). When pushed to GitHub, it automatically spins up Windows, macOS, and Linux virtual environments and publishes compiled standalone binaries on every release.

---

## License

This project is free software, licensed under the **GNU Affero General Public License v3.0 or later** (AGPL-3.0-or-later). See the [COPYING.md](COPYING.md) file for the full license text.

Copyright (c) 2026 Joel Benway
