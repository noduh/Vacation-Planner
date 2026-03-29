import folium
import pandas as pd
from api_client import get_osrm_route

def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def format_distance(meters: float) -> str:
    km = meters / 1000
    return f"{km:.2f} km"

def build_map(start_lat: float, start_lon: float, locations_df: pd.DataFrame) -> folium.Map:
    """Builds the interactive folium map with custom javascript for toggling routes."""
    m = folium.Map(
        location=[start_lat, start_lon], 
        zoom_start=12,
        tiles='CartoDB positron'
    )
    
    # Start marker
    start_marker = folium.Marker(
        [start_lat, start_lon],
        popup=folium.Popup("<b>Start Location</b>", max_width=250),
        icon=folium.Icon(color="green", icon="play", prefix='glyphicon')
    )
    start_marker.add_to(m)

    js_click_handlers = []
    all_route_vars = []
    
    # Create FeatureGroups for each category
    categories = locations_df['category'].unique().tolist() if 'category' in locations_df.columns else ['Uncategorized']
    category_groups = {cat: folium.FeatureGroup(name=f" {cat}") for cat in categories}
    
    for cat_name, group in category_groups.items():
        group.add_to(m)

    for index, row in locations_df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        label = row['label']
        desc = row.get('description', '')
        category = row.get('category', 'Uncategorized')
        pin_color = row.get('color', 'red')
        
        # Validate color for folium
        valid_colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 
                        'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 
                        'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        if pin_color not in valid_colors:
            pin_color = 'red'
            
        route_coords, dist, duration = get_osrm_route(start_lat, start_lon, lat, lon)
        
        popup_html = f"<b>{label}</b><br>{desc}"
        if route_coords:
            popup_html += f"<br><br><b>Distance:</b> {format_distance(dist)}"
            popup_html += f"<br><b>Travel Time:</b> {format_time(duration)}"
            
        marker = folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=pin_color, icon="info-sign", prefix='glyphicon')
        )
        marker.add_to(category_groups[category])
        
        if route_coords:
            route_line = folium.PolyLine(
                route_coords,
                color="#0066FF",
                weight=5,
                opacity=0.0 # Initially hidden
            )
            route_line.add_to(category_groups[category])
            
            route_var = route_line.get_name()
            marker_var = marker.get_name()
            all_route_vars.append(route_var)
            
            js_click_handlers.append(f"""
            {marker_var}.on('click', function(e) {{
                // Hide all routes first
                all_routes_arr.forEach(function(r) {{
                    r.setStyle({{opacity: 0.0}});
                }});
                // Show this specific route
                {route_var}.setStyle({{opacity: 0.8}});
            }});
            """)

    if all_route_vars:
        routes_array_str = "var all_routes_arr = [" + ", ".join(all_route_vars) + "];"
        handlers_str = "\n".join(js_click_handlers)
        
        custom_js = f"""
        <script>
        // Setup function
        function setupVacationMapInteraction() {{
            if (typeof all_routes_arr !== 'undefined') return; // already ran
            
            {routes_array_str}
            {handlers_str}
            
            // Clicking elsewhere on the map to clear route selection
            for (var key in window) {{
                if (key.startsWith("map_") && window[key] instanceof L.Map) {{
                    window[key].on('click', function(e) {{
                        if (typeof all_routes_arr !== 'undefined') {{
                            all_routes_arr.forEach(function(r) {{
                                r.setStyle({{opacity: 0.0}});
                            }});
                        }}
                    }});
                    break;
                }}
            }}
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            setTimeout(setupVacationMapInteraction, 800);
        }});
        // Fallback execution after slightly longer delay
        setTimeout(setupVacationMapInteraction, 1500);
        setTimeout(setupVacationMapInteraction, 3000);
        </script>
        """
        m.get_root().html.add_child(folium.Element(custom_js))

    # Add Layer Control to handle categories
    folium.LayerControl(collapsed=False).add_to(m)

    return m
