import requests
from geopy.geocoders import Nominatim

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

def get_coordinates(address: str):
    """Geocodes an address to latitude and longitude."""
    geolocator = Nominatim(user_agent="vacation_planner_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def get_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    """
    Fetches the driving route between two points using the OSRM public API.
    Returns: coords (list of [lat, lon]), distance (meters), duration (seconds)
    """
    url = f"{OSRM_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        req = requests.get(url, timeout=60)
        req.raise_for_status()
        data = req.json()
        if data.get("code") == "Ok" and "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]
            # GeoJSON coordinates are [lon, lat], Folium needs it as [lat, lon]
            coords = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
            distance = route.get("distance", 0)
            duration = route.get("duration", 0)
            return coords, distance, duration
    except Exception as e:
        print(f"Routing API error: {e}")
    
    return None, 0, 0
