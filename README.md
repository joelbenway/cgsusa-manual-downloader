# CGSUSA Materials Manual PDF Downloader

An automated tool to download and organize all Catechesis of the Good Shepherd (CGSUSA) Materials Manual PDFs into structured folders ready for printing.

## Directory Structure

Files are organized matching the natural CGS atrium structure:

```text
cgsusa/
├── level 1/
│   ├── Incarnation Geography of Israel/
│   │   ├── Globe and Raised Surface Map of Israel/
│   │   │   ├── 1-Directions_for_Israel_Raised-Surface-Wall...pdf
│   │   │   ├── 1-GEO_Raised_Surface_Model_DIR_2014.pdf
│   │   │   └── Raised_Surface_Collage_PIeces___Symbols2.pdf
│   │   └── Puzzle Map of Israel/
│   │       └── 1-Regions_Puzzle_DIRECTIONS_2014-1.pdf
│   ├── Incarnation Prophecies/
│   ├── Baptism/
│   ├── Eucharist/
│   ├── Kingdom of God Parables/
│   └── Liturgical Calendar/
├── level 2/
└── level 3/
```

---

## Running on Windows

### Standalone Executable (No Python Required)
A precompiled portable executable is available directly in this folder:
- [cgsusa_manual_downloader.exe](file:///c:/Users/Joel%20Benway/Documents/cgsusa/cgsusa_manual_downloader.exe)

You can send this `.exe` file to any catechist or colleague with Windows. They do not need Python or any packages installed.
1. **Double-click** `cgsusa_manual_downloader.exe`.
2. It prompts for your CGSUSA email and password.
3. Automatically downloads all levels right next to the `.exe`.

### Or via Python:
```powershell
.\venv\Scripts\activate
python download_manuals.py
```

---

## Running on macOS

PyInstaller cannot cross-compile a macOS binary directly from a Windows machine (because macOS binaries require Apple's native dynamic libraries and frameworks). However, you have two great options for Mac users:

### Option A: One-Click Mac Launcher (`run_mac.command`)
For Mac catechists who just want to double-click:
1. Send them the folder containing `download_manuals.py`, `requirements.txt`, and [run_mac.command](file:///c:/Users/Joel%20Benway/Documents/cgsusa/run_mac.command).
2. On macOS, **double-clicking** `run_mac.command` will automatically open Terminal, configure the environment, and run the downloader seamlessly.
   *(First-time permission if needed: `chmod +x run_mac.command`)*

### Option B: Build a Standalone Mac Binary with PyInstaller
If you or a colleague have a Mac, run:
```bash
bash build_mac.sh
```
This builds the native macOS standalone binary in `dist/cgsusa_manual_downloader`.

### Option C: Automated Cloud Build via GitHub Actions
A workflow is already configured in [.github/workflows/ci.yaml](file:///c:/Users/Joel%20Benway/Documents/cgsusa/.github/workflows/ci.yaml). When pushed to GitHub, GitHub Actions will automatically spin up macOS, Windows, and Linux virtual machines in the cloud and compile native executables for all three platforms.

---

## Command Line Options

Both the `.exe` and the `.py` script support the same options:

| Flag | Description |
|---|---|
| *(no arguments)* | Automatically downloads **all levels** (Level 1, 2, and 3) |
| `--level 1` / `2` / `3` / `all` | Download a specific level or all (default: `all`) |
| `--version` | Display program version (v1.0.0) |
| `--help` | Display help and usage details |
| `--outdir <path>` | Specify custom output folder |
| `--no-cache` | Force a new login instead of using cached session |
| `--no-pause` | Don't pause for Enter before exiting |

### Examples:

```powershell
# Show version
.\cgsusa_manual_downloader.exe --version

# Show help
.\cgsusa_manual_downloader.exe --help

# Download all levels (default)
.\cgsusa_manual_downloader.exe

# Download only Level 1
.\cgsusa_manual_downloader.exe --level 1
```

---

## Features & Reliability

- **Session Caching**: Remembers login in `cgsusa_session.json` so passwords don't need to be re-entered.
- **Smart Resume**: Automatically detects existing files by size and skips them, allowing safe re-runs anytime.
- **Auto-Retry & Resilience**: Automatically handles temporary network hiccups or server connection drops (`WinError 10054`) with exponential retry.
