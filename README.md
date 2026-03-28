# Interactive Trip Planning Map

An open-source Python tool built with Streamlit and Folium to plan road trips. It takes a starting location and a CSV of destinations, plots them on an interactive Leaflet map, fetches driving directions using the public OSRM API, and provides an exportable standalone HTML map file.

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
3. Run the Streamlit application:
   ```bash
   python -m streamlit run src/app.py
   ```
4. A web page will automatically open in your default browser at `http://localhost:8501`.

## Usage
- Provide your starting address or coordinates in the sidebar.
- Choose to use the default `sample_destinations.csv`, or upload your own CSV file containing headers `label`, `latitude`, `longitude`, and `description`.
- Click the map pins to view the isolated navigation directions for each destination.
- Click "Download Map as HTML" to save a mobile and desktop friendly version of your trip map that works completely offline without needing the Python server!

## Testing
To verify the API integrations, run the included tests:
```bash
python tests.py
```
