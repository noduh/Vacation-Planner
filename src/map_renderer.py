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
    """Builds the interactive folium map with responsive purple styling."""
    
    # Define Tile Layers
    tiles = {
        "Light Mode": folium.TileLayer(
            tiles='CartoDB positron',
            name="Light Mode",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        ),
        "Dark Mode": folium.TileLayer(
            tiles='CartoDB dark_matter',
            name="Dark Mode",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        ),
        "Satellite View": folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            name="Satellite View",
            attr='Tiles &copy; Esri'
        )
    }

    m = folium.Map(
        location=[start_lat, start_lon], 
        zoom_start=12,
        tiles=None
    )
    
    # Default to Light Mode
    tiles["Light Mode"].add_to(m)
    tiles["Dark Mode"].add_to(m)
    tiles["Satellite View"].add_to(m)
    
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
                color="#a855f7", # Purple route
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
        function toggleLayer(layerVar, checked) {{
            if (checked) {{
                layerVar.addTo(current_map);
            }} else {{
                current_map.removeLayer(layerVar);
            }}
        }}

        function toggleCategory(catId, checked) {{
            const catGroup = window['group_' + catId];
            if (catGroup) {{
                if (checked) catGroup.addTo(current_map);
                else current_map.removeLayer(catGroup);
            }}
            // Sync children checkboxes
            document.querySelectorAll('.cat-' + catId + '-item').forEach(cb => {{
                cb.checked = checked;
            }});
        }}

        function setupVacationMapInteraction() {{
            if (window.map_initialized) return;
            
            // Find the map instance
            for (var key in window) {{
                if (key.startsWith("map_") && window[key] instanceof L.Map) {{
                    window.current_map = window[key];
                    break;
                }}
            }}
            
            if (!current_map) return;
            window.map_initialized = true;
            
            {routes_array_str}
            {handlers_str}
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            setTimeout(setupVacationMapInteraction, 500);
        }});
        </script>
        """
        m.get_root().html.add_child(folium.Element(custom_js))

    # --- PREMIUM STYLING INJECTION (PURPLE) ---
    premium_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

    body { font-family: 'Outfit', sans-serif !important; margin: 0; padding: 0; }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(168, 85, 247, 0.4); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(168, 85, 247, 0.6); }

    /* Trip Dashboard (Top-Left) */
    .trip-dashboard {
        position: absolute;
        top: 20px;
        left: 20px;
        z-index: 1001;
        background: rgba(26, 12, 58, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 16px;
        padding: 15px 20px;
        color: white;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        width: 260px;
        pointer-events: auto;
    }
    .trip-dashboard h1 { margin: 0; font-size: 20px; font-weight: 600; color: #e9d5ff; }
    .trip-dashboard p { margin: 5px 0 0 0; font-size: 13px; opacity: 0.8; color: #f3e8ff; }

    /* Custom Trip Explorer Sidebar (Right) */
    .trip-explorer {
        position: absolute;
        top: 20px;
        right: 20px;
        bottom: 20px;
        z-index: 1001;
        width: 300px;
        background: rgba(26, 12, 58, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 20px;
        padding: 20px;
        color: white;
        box-shadow: 0 15px 50px rgba(0,0,0,0.6);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .explorer-header { font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #e9d5ff; display: flex; align-items: center; justify-content: space-between; }
    .explorer-content { flex: 1; overflow-y: auto; padding-right: 5px; }

    .category-group { margin-bottom: 15px; border-radius: 12px; background: rgba(168, 85, 247, 0.05); overflow: hidden; }
    .category-label { 
        padding: 12px 15px; background: rgba(168, 85, 247, 0.1); display: flex; align-items: center; cursor: pointer;
        transition: background 0.2s;
    }
    .category-label:hover { background: rgba(168, 85, 247, 0.2); }
    .category-label input { margin-right: 12px; accent-color: #a855f7; width: 16px; height: 16px; cursor: pointer; }
    .category-title { flex: 1; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
    .category-toggle-icon { font-size: 10px; opacity: 0.5; transition: transform 0.3s; }
    
    .location-list { display: none; padding: 5px 0; }
    .location-list.active { display: block; }
    .category-group.open .category-toggle-icon { transform: rotate(180deg); }

    .location-item { padding: 8px 15px 8px 45px; display: flex; align-items: center; font-size: 13px; opacity: 0.9; transition: opacity 0.2s; }
    .location-item:hover { opacity: 1; background: rgba(168, 85, 247, 0.05); }
    .location-item input { margin-right: 10px; accent-color: #a855f7; width: 14px; height: 14px; cursor: pointer; }

    /* Map Style Selector (Bottom of Explorer) */
    .style-selector { margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(168, 85, 247, 0.2); }
    .style-title { font-size: 12px; font-weight: 600; opacity: 0.5; margin-bottom: 10px; text-transform: uppercase; }
    .style-options { display: flex; gap: 8px; }
    .style-btn { 
        flex: 1; padding: 8px; border-radius: 8px; background: rgba(168, 85, 247, 0.1); border: 1px solid transparent; 
        color: white; font-size: 11px; cursor: pointer; text-align: center; transition: all 0.2s;
    }
    .style-btn:hover { background: rgba(168, 85, 247, 0.2); }
    .style-btn.active { background: #a855f7; border-color: #d8b4fe; }

    /* Mobile Interaction (Slide-out) */
    @media (max-width: 600px) {
        .trip-dashboard { width: calc(100% - 40px); left: 20px; top: 10px; padding: 12px 15px; }
        .trip-explorer { 
            position: fixed; top: auto; bottom: 0; left: 0; right: 0; width: 100%; height: 50vh; 
            border-radius: 20px 20px 0 0; z-index: 2000; border-bottom: none;
        }
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(premium_css))

    # Build the Explorer Sidebar HTML
    import json
    
    explorer_html = f"""
    <div class="trip-explorer" id="tripExplorer">
        <div class="explorer-header">
            <span>Trip Explorer</span>
        </div>
        <div class="explorer-content">
    """
    
    for cat, group in category_groups.items():
        cat_id = cat.replace(" ", "_").lower()
        # Add the group to window for JS access
        m.get_root().html.add_child(folium.Element(f"<script>window['group_{cat_id}'] = {group.get_name()};</script>"))
        
        explorer_html += f"""
        <div class="category-group" id="catGroup_{cat_id}">
            <div class="category-label">
                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategory('{cat_id}', this.checked)">
                <div class="category-title" onclick="document.getElementById('locList_{cat_id}').classList.toggle('active'); document.getElementById('catGroup_{cat_id}').classList.toggle('open')">{cat}</div>
                <span class="category-toggle-icon">▼</span>
            </div>
            <div class="location-list" id="locList_{cat_id}">
        """
        
        cat_items = locations_df[locations_df['category'] == cat] if 'category' in locations_df.columns else locations_df
        for idx, row in cat_items.iterrows():
            # Find the marker variable name (this is a bit hacky but folium doesn't expose it easily)
            # We'll just use a general toggle if we can't find specific markers easily
            explorer_html += f"""
                <div class="location-item">
                    <span>{row['label']}</span>
                </div>
            """
        
        explorer_html += "</div></div>"

    # Add Map style selectors
    explorer_html += """
        </div>
        <div class="style-selector">
            <div class="style-title">Base Map</div>
            <div class="style-options">
                <div class="style-btn active" onclick="switchMapStyle('Light', this)">Light</div>
                <div class="style-btn" onclick="switchMapStyle('Dark', this)">Dark</div>
                <div class="style-btn" onclick="switchMapStyle('Satellite', this)">Sat</div>
            </div>
        </div>
    </div>
    
    <script>
    function switchMapStyle(style, btn) {
        document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Find existing tile layers and toggle them
        current_map.eachLayer(function(l) {
            if (l instanceof L.TileLayer) current_map.removeLayer(l);
        });
        
        let url, attr;
        if (style === 'Light') {
            url = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
            attr = '&copy; CARTO';
        } else if (style === 'Dark') {
            url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
            attr = '&copy; CARTO';
        } else {
            url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
            attr = 'Tiles &copy; Esri';
        }
        L.tileLayer(url, {attribution: attr}).addTo(current_map);
    }
    </script>
    """
    m.get_root().html.add_child(folium.Element(explorer_html))

    dashboard_html = f"""
    <div class="trip-dashboard">
        <h1>Vacation Planner</h1>
        <p>Exploring <b>{len(locations_df)}</b> destinations.<br>Tap a pin to see travel times.</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(dashboard_html))

    return m
