# Vacation Planner

A modern Python desktop application for planning vacations and road trips. Enter a starting location, import a CSV of destinations, and generate a beautiful, standalone interactive HTML map — complete with driving routes, travel times, and a filterable sidebar.

> **🤖 Note:** This project was almost entirely programmed by AI (vibe-coded).

## ✨ Features
- **Modern Dashboard**: A vibrant, purple-themed GUI built with CustomTkinter.
- **Flexible Starting Point**: Enter a starting address *or* raw latitude/longitude coordinates.
- **CSV Import**: Load any CSV of destinations and instantly build a full trip map.
- **Interactive HTML Export**: Generates a standalone, mobile-responsive HTML map with a **Trip Explorer** sidebar and per-category toggles.
- **Smart Routing**: Fetches driving directions and travel times automatically via the OSRM API (no API key required).

## 📥 Download a Pre-Built Binary (Recommended for Users)

Pre-built, single-file executables are available for **Windows**, **macOS**, and **Linux** on the [Releases page](https://github.com/noduh/Vacation-Planner/releases).

1. Go to the [latest release](https://github.com/noduh/Vacation-Planner/releases/latest).
2. Download the binary for your operating system:
   - `VacationPlanner-<version>-Windows.exe` — Windows
   - `VacationPlanner-<version>-macOS` — macOS
   - `VacationPlanner-<version>-Linux` — Linux
3. Run the downloaded file directly — no Python installation required.

> **macOS / Linux:** You may need to mark the file as executable first:
> ```bash
> chmod +x VacationPlanner-*-macOS   # or -Linux
> ./VacationPlanner-*-macOS
> ```

> **Linux prerequisite:** The binary requires certain system libraries. If the app fails to launch, install `tkinter`:
> ```bash
> sudo apt-get install python3-tk   # Debian / Ubuntu
> sudo dnf install python3-tkinter  # Fedora / RHEL
> ```

## 🚀 Developer Setup

### Prerequisites

> **Linux:** `tkinter` is not bundled with Python on most Linux distributions. Install it first:
> ```bash
> sudo apt-get install python3-tk   # Debian / Ubuntu
> sudo dnf install python3-tkinter  # Fedora / RHEL
> ```

### Using pip

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install the project and its dependencies
pip install .
```

### Using uv

```bash
uv sync
```

## 🛠️ How to Run (from source)

After installing, launch the app with either command:

```bash
vacation-planner
# or
python -m src.main
```

## 📦 Building a Standalone Binary

Binaries are built automatically via CI on every tagged release. To build one locally:

```bash
pip install ".[build]"

# macOS / Linux
pyinstaller --noconfirm --onefile --windowed \
  --name "VacationPlanner" \
  --add-data "src/data:data" \
  --hidden-import src.api_client \
  --hidden-import src.map_renderer \
  --collect-all customtkinter \
  --collect-all folium \
  --collect-all branca \
  --collect-all geopy \
  --collect-all pandas \
  --collect-all requests \
  VacationPlanner.py

# Windows (PowerShell)
pyinstaller --noconfirm --onefile --windowed `
  --name "VacationPlanner" `
  --add-data "src/data;data" `
  --hidden-import src.api_client `
  --hidden-import src.map_renderer `
  --collect-all customtkinter `
  --collect-all folium `
  --collect-all branca `
  --collect-all geopy `
  --collect-all pandas `
  --collect-all requests `
  VacationPlanner.py
```

The output binary will be in the `dist/` folder.

## 📂 CSV Data Format

The app ships with a sample `vacation_destinations.csv`. Your own CSV must include these columns:

| Column | Required | Description |
|---|---|---|
| `label` | ✅ | Name of the destination |
| `latitude` | ✅ | Decimal latitude |
| `longitude` | ✅ | Decimal longitude |
| `category` | ❌ | Group label (e.g., Dining, Sightseeing) — used for sidebar filters |
| `description` | ❌ | Text shown in the map popup |

---
*Note: The native UI is optimized for laptop screens; exported maps are fully responsive for mobile devices.*
