# Vacation Planner

A modern, high-end Python desktop application for planning vacations and road trips. Built with **CustomTkinter** and **Folium**, it transforms your destination lists into beautiful, interactive travel dashboards.

## ✨ Features
- **Modern Dashboard**: A vibrant, purple-themed GUI designed for focus and readability.
- **Simplified Workflow**: Direct CSV import—quickly transform your entire destination list into a map.
- **Professional Exports**: Generates a standalone, mobile-responsive HTML map with a custom **Trip Explorer** sidebar and category toggles.
- **Glassmorphism Design**: High-end translucent UI elements across both the app and exported documents.
- **Smart Routing**: Fetches driving directions and travel times automatically via the OSRM API.

## 🚀 Setup and Installation

> **Linux prerequisite:** `tkinter` is not bundled with Python on most Linux distributions. Install it before proceeding:
> ```bash
> sudo apt-get install python3-tk   # Debian / Ubuntu
> sudo dnf install python3-tkinter  # Fedora / RHEL
> ```

### Using pip (recommended)

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install the project and its dependencies
pip install .
```

### Using uv

```bash
uv sync
```

## 🛠️ How to Run

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Run the application:
   ```bash
   python -m src.main
   ```

## 📦 Creating a Standalone Binary
To build a portable version for your OS:
```bash
.venv/bin/pyinstaller --noconfirm --onefile --windowed --name "VacationPlanner" --add-data "src/data:data" --collect-all customtkinter --collect-all folium --collect-all branca --collect-all geopy --collect-all pandas --collect-all requests VacationPlanner.py
```

## 📂 Data Format
Your `vacation_destinations.csv` should include the following headers:
- `label`: Name of the destination
- `latitude`: Decimal latitude
- `longitude`: Decimal longitude
- `category`: Group (e.g., Dining, Sightseeing)
- `description`: (Optional) Details for the popup

---
*Note: The native UI is optimized for laptop screens but the exported maps are fully responsive for mobile devices.*
