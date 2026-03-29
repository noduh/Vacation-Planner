import streamlit as st
import pandas as pd
import io
import os
import streamlit.components.v1 as components

from api_client import get_coordinates
from map_renderer import build_map

st.set_page_config(page_title="Trip Planning Map", layout="wide", page_icon="🗺️")

st.title("🗺️ Interactive Trip Planning Map")
st.markdown("Plan your trips by providing a starting location and a CSV file of destinations. Click on the destination markers to see route details and travel time!")

with st.sidebar:
    st.header("1. Input Starting Location")
    start_location_type = st.radio("Location Type:", ["Coordinates (Lat, Lon)", "Address/City"])

    start_lat, start_lon = None, None

    if start_location_type == "Address/City":
        address = st.text_input("Enter starting address", "San Francisco, CA")
        if address:
            with st.status("Geocoding..."):
                lat, lon = get_coordinates(address)
                if lat and lon:
                    start_lat, start_lon = lat, lon
                    st.write(f"Found Coordinates: {lat:.6f}, {lon:.6f}")
                else:
                    st.error("Could not find location. Try another address.")
    else:
        col1, col2 = st.columns(2)
        start_lat = col1.number_input("Latitude", value=37.7749, format="%.6f")
        start_lon = col2.number_input("Longitude", value=-122.4194, format="%.6f")

    st.header("2. Upload Destinations CSV")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    st.info("CSV must contain columns: `label`, `latitude`, `longitude`. Optional: `description`.")

    default_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_destinations.csv")
    
    if uploaded_file:
        try:
            locations_df = pd.read_csv(uploaded_file)
            req_cols = ['label', 'latitude', 'longitude']
            if not all(col in locations_df.columns for col in req_cols):
                st.error(f"CSV must contain at least these columns: {', '.join(req_cols)}")
            else:
                st.session_state.locations_df = locations_df
                st.success("Loaded uploaded CSV.")
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
    else:
        if os.path.exists(default_data_path):
            if st.button("Use Sample Data"):
                locations_df = pd.read_csv(default_data_path)
                st.session_state.locations_df = locations_df
                st.success("Loaded sample destinations.")

if start_lat and start_lon and 'locations_df' in st.session_state:
    locations_df = st.session_state.locations_df
    
    if st.button("Generate Map", type="primary"):
        with st.spinner("Fetching routes and generating map..."):
            interactive_map = build_map(start_lat, start_lon, locations_df)
            
            # Save the map for download
            map_html = io.BytesIO()
            interactive_map.save(map_html, close_file=False)
            map_html.seek(0)
            st.session_state.map_html = map_html
            st.session_state.interactive_map = interactive_map

if 'interactive_map' in st.session_state:
    st.markdown("### Output Map")
    
    # We use Streamlit native HTML component to ensure our custom Leaflet
    # javascript executes perfectly in the web app, exactly as it does
    # in the exported HTML!
    styled_map = st.session_state.interactive_map.get_root().render()
    components.html(styled_map, width=None, height=600)
    
    st.download_button(
        label="📥 Download Map as HTML (Mobile Friendly)",
        data=st.session_state.map_html,
        file_name="trip_planning_map.html",
        mime="text/html",
        help="You can open this HTML file directly in any web browser without needing python."
    )
    
    st.markdown("> **Tip:** Make sure to click on the pins to view the custom navigation routes and travel information!")
