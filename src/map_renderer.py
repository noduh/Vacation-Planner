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
        tiles=None,
        zoom_control=False
    )
    
    # Add zoom control at bottom-left via JS injection
    m.get_root().html.add_child(folium.Element("""
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        setTimeout(function() {
            for (var key in window) {
                if (key.startsWith("map_") && window[key] instanceof L.Map) {
                    L.control.zoom({position: 'bottomleft'}).addTo(window[key]);
                    break;
                }
            }
        }, 300);
    });
    </script>
    """))
    
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
    marker_vars_by_cat = {}  # { cat_id: [marker_var, ...] }
    route_vars_by_marker = {}  # { marker_var: route_var }
    
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
        cat_id = category.replace(" ", "_").lower()
        if cat_id not in marker_vars_by_cat:
            marker_vars_by_cat[cat_id] = []
        marker_vars_by_cat[cat_id].append(marker.get_name())
        
        if route_coords:
            route_line = folium.PolyLine(
                route_coords,
                color="#a855f7",
                weight=5,
                opacity=0.0
            )
            route_line.add_to(category_groups[category])
            
            route_var = route_line.get_name()
            marker_var = marker.get_name()
            all_route_vars.append(route_var)
            route_vars_by_marker[marker_var] = route_var
            
            js_click_handlers.append(f"""
            {marker_var}.on('click', function(e) {{
                all_routes_arr.forEach(function(r) {{ r.setStyle({{opacity: 0.0}}); }});
                {route_var}.setStyle({{opacity: 0.8}});
            }});
            """)

    # Build marker registry JS — exposes per-location marker vars for checkbox toggling
    marker_registry_lines = []
    for cat_id, mvars in marker_vars_by_cat.items():
        for i, mvar in enumerate(mvars):
            route_var = route_vars_by_marker.get(mvar, "null")
            marker_registry_lines.append(
                f"window._markers.push({{catId:'{cat_id}', idx:{i}, marker:{mvar}, route:{route_var}}});"
            )

    if all_route_vars:
        routes_array_str = "var all_routes_arr = [" + ", ".join(all_route_vars) + "];"
        handlers_str = "\n".join(js_click_handlers)
    else:
        routes_array_str = "var all_routes_arr = [];"
        handlers_str = ""

    # Find map early so toggleCategory/toggleLocation can use current_map immediately
    find_map_js = """
    <script>
    window._markers = [];
    // Resolve map reference as soon as Leaflet initialises it
    (function waitForMap() {
        for (var key in window) {
            if (key.startsWith('map_') && window[key] instanceof L.Map) {
                window.current_map = window[key]; return;
            }
        }
        setTimeout(waitForMap, 50);
    })();

    function toggleCategory(catId, checked) {
        var catGroup = window['group_' + catId];
        if (catGroup) {
            if (checked) catGroup.addTo(window.current_map);
            else window.current_map.removeLayer(catGroup);
        }
        // Sync every location checkbox in this category
        document.querySelectorAll('.loc-cb-' + catId).forEach(function(cb) {
            cb.checked = checked;
        });
    }

    function toggleLocation(catId, idx, checked) {
        var entry = window._markers.find(function(m) { return m.catId === catId && m.idx === idx; });
        if (!entry) return;
        if (checked) {
            entry.marker.addTo(window.current_map);
        } else {
            window.current_map.removeLayer(entry.marker);
            if (entry.route && entry.route !== null) {
                entry.route.setStyle({opacity: 0.0});
            }
        }
        // Update category master checkbox
        var anyChecked = Array.from(document.querySelectorAll('.loc-cb-' + catId)).some(function(cb) { return cb.checked; });
        var catCb = document.querySelector('.cat-cb-' + catId);
        if (catCb) catCb.checked = anyChecked;
    }

    function setupRouteClicks() {
        if (window.routes_initialized) return;
        if (!window.current_map) { setTimeout(setupRouteClicks, 100); return; }
        window.routes_initialized = true;
        """ + routes_array_str + """
        """ + handlers_str + """
    }

    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            """ + "\n".join(marker_registry_lines) + """
            setupRouteClicks();
        }, 600);
    });
    </script>
    """
    m.get_root().html.add_child(folium.Element(find_map_js))

    # --- PREMIUM STYLING INJECTION (PURPLE) ---
    premium_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

    body { font-family: 'Outfit', sans-serif !important; margin: 0; padding: 0; overflow: hidden; }
    
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

    /* Sidebar collapse: no external toggle button, button lives in header */
    /* Custom Trip Explorer Sidebar (Right) */
    .trip-explorer {
        position: absolute;
        top: 20px;
        right: 20px;
        bottom: 20px;
        z-index: 1001;
        width: 320px;
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
        transform: translateX(0);
        transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        /* Keep collapsed panel from causing page overflow */
        clip-path: inset(0 round 20px);
    }
    .trip-explorer.collapsed {
        transform: translateX(calc(100% + 40px));
        /* pointer-events off so map is interactive when hidden */
        pointer-events: none;
    }

    .explorer-header {
        font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #e9d5ff;
        display: flex; align-items: center; justify-content: space-between;
    }
    .explorer-collapse-btn {
        width: 28px; height: 28px; border-radius: 8px; cursor: pointer;
        background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.25);
        color: #e9d5ff; font-size: 16px; display: flex; align-items: center; justify-content: center;
        transition: background 0.2s; flex-shrink: 0;
    }
    .explorer-collapse-btn:hover { background: rgba(168, 85, 247, 0.3); }
    .explorer-content { flex: 1; overflow-y: auto; padding-right: 5px; }

    .category-group { margin-bottom: 12px; border-radius: 12px; background: rgba(168, 85, 247, 0.05); overflow: hidden; }
    .category-label { 
        padding: 12px 15px; background: rgba(168, 85, 247, 0.1); display: flex; align-items: center; cursor: pointer;
        transition: background 0.2s; gap: 0;
    }
    .category-label:hover { background: rgba(168, 85, 247, 0.2); }
    .category-label input[type="checkbox"] { 
        flex-shrink: 0; accent-color: #a855f7; width: 16px; height: 16px; cursor: pointer; margin: 0;
    }
    .category-title { 
        flex: 1; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;
        margin-left: 10px;
    }
    .category-toggle-icon { font-size: 10px; opacity: 0.5; transition: transform 0.3s; flex-shrink: 0; }
    
    .location-list { display: none; padding: 5px 0; }
    .location-list.active { display: block; }
    .category-group.open .category-toggle-icon { transform: rotate(180deg); }

    .location-item { 
        padding: 8px 15px 8px 20px; display: flex; align-items: center; font-size: 13px; opacity: 0.9; 
        transition: opacity 0.2s; gap: 0;
    }
    .location-item:hover { opacity: 1; background: rgba(168, 85, 247, 0.05); }
    .location-item input[type="checkbox"] { 
        flex-shrink: 0; accent-color: #a855f7; width: 14px; height: 14px; cursor: pointer; margin: 0;
    }
    .location-item span { margin-left: 10px; }

    /* Map Style Dropdown */
    .style-selector { margin-top: auto; padding-top: 15px; border-top: 1px solid rgba(168, 85, 247, 0.2); }
    .style-title { font-size: 11px; font-weight: 600; opacity: 0.5; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .style-dropdown {
        width: 100%; padding: 10px 14px; border-radius: 10px; 
        background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25);
        color: white; font-size: 13px; font-family: 'Outfit', sans-serif;
        cursor: pointer; appearance: none; -webkit-appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23e9d5ff' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10z'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 12px center;
        outline: none; transition: border-color 0.2s;
    }
    .style-dropdown:hover { border-color: rgba(168, 85, 247, 0.5); }
    .style-dropdown:focus { border-color: #a855f7; }
    .style-dropdown option { background: #1a0c3a; color: white; }

    /* Mobile Interaction */
    @media (max-width: 600px) {
        .trip-dashboard { width: calc(100% - 40px); left: 20px; top: 10px; padding: 12px 15px; }
        .trip-explorer { 
            position: fixed; top: auto; bottom: 0; left: 0; right: 0; width: 100%; height: 55vh; 
            border-radius: 20px 20px 0 0; z-index: 2000; border-bottom: none;
            transform: translateY(0);
            clip-path: none;
        }
        .trip-explorer.collapsed {
            transform: translateY(100%);
        }
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(premium_css))

    # Build the Explorer Sidebar HTML
    # Also expose category groups to JS (for toggleCategory)
    for cat, group in category_groups.items():
        cat_id = cat.replace(" ", "_").lower()
        m.get_root().html.add_child(folium.Element(f"<script>window['group_{cat_id}'] = {group.get_name()};</script>"))

    explorer_html = """
    <div class="trip-explorer" id="tripExplorer">
        <div class="explorer-header">
            <span>Trip Explorer</span>
            <button class="explorer-collapse-btn" id="explorerCollapseBtn" onclick="toggleSidebar()">&#8250;</button>
        </div>
        <div class="explorer-content">
    """

    for cat, group in category_groups.items():
        cat_id = cat.replace(" ", "_").lower()
        cat_markers = marker_vars_by_cat.get(cat_id, [])

        explorer_html += f"""
        <div class="category-group" id="catGroup_{cat_id}">
            <div class="category-label" onclick="document.getElementById('locList_{cat_id}').classList.toggle('active'); document.getElementById('catGroup_{cat_id}').classList.toggle('open')">
                <input type="checkbox" checked class="cat-cb-{cat_id}" onclick="event.stopPropagation(); toggleCategory('{cat_id}', this.checked)">
                <div class="category-title">{cat}</div>
                <span class="category-toggle-icon">&#9660;</span>
            </div>
            <div class="location-list" id="locList_{cat_id}">
        """

        cat_items = locations_df[locations_df['category'] == cat] if 'category' in locations_df.columns else locations_df
        for i, (idx, row) in enumerate(cat_items.iterrows()):
            explorer_html += f"""
                <div class="location-item">
                    <input type="checkbox" checked class="loc-cb-{cat_id}" onclick="toggleLocation('{cat_id}', {i}, this.checked)">
                    <span>{row['label']}</span>
                </div>
            """

        explorer_html += "</div></div>"

    # Map style dropdown + collapse re-open button
    explorer_html += """
        </div>
        <div class="style-selector">
            <div class="style-title">Base Map</div>
            <select class="style-dropdown" id="mapStyleSelect" onchange="switchMapStyle(this.value)">
                <option value="Light" selected>Light Mode</option>
                <option value="Dark">Dark Mode</option>
                <option value="Satellite">Satellite View</option>
            </select>
        </div>
    </div>

    <!-- Re-open button visible only when collapsed -->
    <button id="explorerOpenBtn" onclick="toggleSidebar()"
        style="display:none; position:absolute; top:20px; right:20px; z-index:1002;
               width:44px; height:44px; border-radius:12px; cursor:pointer;
               background:rgba(26,12,58,0.85); border:1px solid rgba(168,85,247,0.3);
               color:#e9d5ff; font-size:22px; align-items:center; justify-content:center;
               box-shadow:0 8px 30px rgba(0,0,0,0.4); backdrop-filter:blur(16px);
               -webkit-backdrop-filter:blur(16px);">&#8249;</button>

    <script>
    function toggleSidebar() {
        var explorer = document.getElementById('tripExplorer');
        var colBtn   = document.getElementById('explorerCollapseBtn');
        var openBtn  = document.getElementById('explorerOpenBtn');
        var collapsed = explorer.classList.toggle('collapsed');
        colBtn.innerHTML = collapsed ? '&#8249;' : '&#8250;';
        openBtn.style.display = collapsed ? 'flex' : 'none';
    }

    function switchMapStyle(style) {
        window.current_map.eachLayer(function(l) {
            if (l instanceof L.TileLayer) window.current_map.removeLayer(l);
        });
        var url, attr;
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
        L.tileLayer(url, {attribution: attr}).addTo(window.current_map);
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
