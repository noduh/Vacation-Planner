# Interactive Vacation Planning Map

An open-source Python native desktop application built with CustomTkinter and Folium to plan road trip vacations. It takes a starting location and a CSV of destinations, plots them on an interactive Leaflet map, fetches driving directions using the public OSRM API, and provides an exportable standalone HTML map file.

## Setup and Installation

This project utilizes a Python virtual environment to manage dependencies locally. 

If installing from scratch:
```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt
```

## How to Run

1. Open your terminal in this repository folder.
2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
3. Run the GUI application:
   ```bash
   python src/main.py
   ```
4. A native desktop window will appear.

## Usage
- Provide your starting address or coordinates.
- Browse to upload your own CSV file containing headers `label`, `latitude`, `longitude`, and optionally `description`.
- Click 'Generate Map' to automatically fetch routes and save your `vacation_planning_map.html` offline map locally.

*Note: The native UI does not require a browser, but compiling with Pyinstaller on Linux requires `python3-tk`.*
