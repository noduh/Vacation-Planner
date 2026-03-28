import sys
import os
import pandas as pd

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from api_client import get_coordinates, get_osrm_route
from map_renderer import build_map

def run_tests():
    print("Starting tests...")
    
    # Test 1: Geocoding
    print("\n[Test 1] Geocoding 'San Francisco, CA'...")
    lat, lon = get_coordinates("San Francisco, CA")
    if lat and lon:
        print(f"Success! Coordinates: ({lat}, {lon})")
    else:
        print("Failed to geocode.")
        sys.exit(1)

    # Test 2: OSRM Routing
    print("\n[Test 2] OSRM Routing from SF to Alcatraz...")
    dest_lat, dest_lon = 37.826977, -122.422955
    coords, dist, duration = get_osrm_route(lat, lon, dest_lat, dest_lon)
    if coords and len(coords) > 0:
        print(f"Success! Received {len(coords)} route coordinates.")
        print(f"Distance: {dist} meters, Duration: {duration} seconds.")
    else:
        print("Failed to get OSRM route.")
        sys.exit(1)

    # Test 3: Folium Map Build
    print("\n[Test 3] Building Folium Map with sample data...")
    csv_path = os.path.join("data", "sample_destinations.csv")
    df = pd.read_csv(csv_path)
    
    try:
        m = build_map(lat, lon, df)
        print("Success! Folium map generated successfully without exceptions.")
    except Exception as e:
        print(f"Failed to build map: {e}")
        sys.exit(1)

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
