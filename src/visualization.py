"""Visualization module for generating interactive Folium maps."""

import math
from pathlib import Path
from typing import Optional

import folium

import config


# Compass segment order (clockwise from top)
COMPASS_ORDER = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def create_formation_rate_map(
    formation_data: dict,
    weather_data: dict,
    output_path: Optional[str] = None,
) -> str:
    """
    Create an interactive map with compass graphics showing formation rates.

    Args:
        formation_data: Dict mapping location names to formation rate data.
                       Each entry has 'rime' and 'verglas' dicts with rates per aspect.
        weather_data: Dict of location weather data.
        output_path: Where to save the HTML file.

    Returns:
        Path to the generated HTML file.
    """
    if output_path is None:
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / config.OUTPUT_MAP_FILENAME)

    # Create base map
    m = folium.Map(
        location=[config.MAP_CENTER["lat"], config.MAP_CENTER["lon"]],
        zoom_start=config.MAP_ZOOM_START,
        tiles="OpenStreetMap",
    )

    # Add terrain layer option
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Topographic",
    ).add_to(m)

    # Add compass markers for each location
    for name, loc_info in config.FOCUS_AREAS.items():
        lat, lon = loc_info["lat"], loc_info["lon"]

        rates = formation_data.get(name, {})
        weather = weather_data.get(name, {})

        # Create compass marker with popup
        _add_compass_marker(m, name, lat, lon, loc_info, rates, weather)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Add legend
    _add_formation_legend(m)

    # Save map
    m.save(output_path)
    print(f"Map saved to: {output_path}")

    return output_path


def _add_compass_marker(
    m: folium.Map,
    name: str,
    lat: float,
    lon: float,
    loc_info: dict,
    rates: dict,
    weather: dict,
) -> None:
    """Add a compass marker with formation rates for a location."""
    rime_rates = rates.get("rime", {})
    verglas_rates = rates.get("verglas", {})

    # Generate SVG compass graphics
    rime_svg = _generate_compass_svg(rime_rates, "Rime")
    verglas_svg = _generate_compass_svg(verglas_rates, "Verglas")

    # Build popup content
    popup_html = f"""
    <div style="min-width: 320px;">
        <h3 style="margin: 0 0 5px 0;">{name}</h3>
        <p style="margin: 0 0 10px 0; color: #666; font-style: italic;">{loc_info.get('description', '')}</p>

        <div style="display: flex; justify-content: space-around; margin-bottom: 15px;">
            <div style="text-align: center;">
                {rime_svg}
            </div>
            <div style="text-align: center;">
                {verglas_svg}
            </div>
        </div>

        {_format_weather_html(weather)}
        {_format_rates_table(rime_rates, verglas_rates)}
    </div>
    """

    popup = folium.Popup(popup_html, max_width=400)

    # Create a combined mini compass for the marker icon
    wind_direction = weather.get("wind_direction", 0)
    wind_speed_ms = weather.get("wind_speed", 0)
    wind_speed_mph = wind_speed_ms * 2.237  # Convert m/s to mph
    altitude = loc_info.get("altitude", 0)
    icon_svg = _generate_mini_compass_icon(rime_rates, verglas_rates, wind_direction, wind_speed_mph, altitude)

    icon = folium.DivIcon(
        html=icon_svg,
        icon_size=(80, 105),
        icon_anchor=(40, 52),
    )

    folium.Marker(
        location=[lat, lon],
        popup=popup,
        tooltip=f"{name} - Click for details",
        icon=icon,
    ).add_to(m)


def _generate_compass_svg(rates: dict, title: str, size: int = 120) -> str:
    """
    Generate an SVG compass graphic with colored segments.

    Args:
        rates: Dict mapping compass direction to formation rate (0-1).
        title: Title to display below compass.
        size: Size of the SVG in pixels.

    Returns:
        SVG string.
    """
    center = size // 2
    outer_radius = (size // 2) - 10
    inner_radius = outer_radius // 3

    segments = []
    labels = []

    for i, direction in enumerate(COMPASS_ORDER):
        rate = rates.get(direction, 0)
        color = _rate_to_color(rate)

        # Calculate segment angles (each segment is 45 degrees)
        # Start from -90 degrees (top) and go clockwise
        start_angle = -90 + (i * 45) - 22.5
        end_angle = start_angle + 45

        # Create path for segment
        path = _create_arc_segment(
            center, center, inner_radius, outer_radius, start_angle, end_angle
        )
        segments.append(f'<path d="{path}" fill="{color}" stroke="#333" stroke-width="1"/>')

        # Add direction label
        label_angle = math.radians(start_angle + 22.5)
        label_radius = outer_radius + 8
        label_x = center + label_radius * math.cos(label_angle)
        label_y = center + label_radius * math.sin(label_angle)
        labels.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="9" font-weight="bold">{direction}</text>'
        )

    # Add wind direction indicator if rates suggest wind
    wind_indicator = ""

    svg = f"""
    <svg width="{size}" height="{size + 20}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{center}" cy="{center}" r="{inner_radius - 2}" fill="#f5f5f5" stroke="#333" stroke-width="1"/>
        {''.join(segments)}
        {''.join(labels)}
        {wind_indicator}
        <text x="{center}" y="{size + 12}" text-anchor="middle" font-size="11" font-weight="bold">{title}</text>
    </svg>
    """
    return svg


def _generate_mini_compass_icon(
    rime_rates: dict,
    verglas_rates: dict,
    wind_direction: float,
    wind_speed_mph: float,
    altitude: int,
) -> str:
    """Generate a dual-compass icon for the map marker with wind direction arrow."""

    def mini_compass(rates: dict, cx: int, cy: int) -> str:
        segments = []
        radius = 14
        inner = 4

        for i, direction in enumerate(COMPASS_ORDER):
            rate = rates.get(direction, 0)
            color = _rate_to_color(rate)
            start_angle = -90 + (i * 45) - 22.5
            end_angle = start_angle + 45
            path = _create_arc_segment(cx, cy, inner, radius, start_angle, end_angle)
            segments.append(f'<path d="{path}" fill="{color}" stroke="#333" stroke-width="0.5"/>')

        return ''.join(segments)

    # Wind arrow rotation: wind_direction is where wind comes FROM
    # Add 180° so arrow points in direction wind is BLOWING (like a flag)
    arrow_rotation = wind_direction + 180

    svg = f"""
    <div style="background: white; border-radius: 5px; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
        <svg width="72" height="95" xmlns="http://www.w3.org/2000/svg">
            <circle cx="18" cy="18" r="3" fill="#eee" stroke="#333" stroke-width="0.5"/>
            {mini_compass(rime_rates, 18, 18)}
            <text x="18" y="38" text-anchor="middle" font-size="8" font-weight="bold">Rime</text>

            <circle cx="54" cy="18" r="3" fill="#eee" stroke="#333" stroke-width="0.5"/>
            {mini_compass(verglas_rates, 54, 18)}
            <text x="54" y="38" text-anchor="middle" font-size="8" font-weight="bold">Verglas</text>

            <!-- Wind direction arrow -->
            <g transform="translate(36, 58)">
                <g transform="rotate({arrow_rotation})">
                    <line x1="0" y1="7" x2="0" y2="-7" stroke="#2563eb" stroke-width="2"/>
                    <polygon points="0,-9 -3,-4 3,-4" fill="#2563eb"/>
                </g>
            </g>
            <text x="36" y="75" text-anchor="middle" font-size="7" font-weight="bold" fill="#2563eb">{wind_speed_mph:.0f} mph</text>
            <text x="36" y="88" text-anchor="middle" font-size="7" font-weight="bold" fill="#666">{altitude}m</text>
        </svg>
    </div>
    """
    return svg


def _create_arc_segment(
    cx: float, cy: float, r_inner: float, r_outer: float,
    start_deg: float, end_deg: float
) -> str:
    """Create SVG path for an arc segment (donut slice)."""
    start_rad = math.radians(start_deg)
    end_rad = math.radians(end_deg)

    # Outer arc points
    x1_outer = cx + r_outer * math.cos(start_rad)
    y1_outer = cy + r_outer * math.sin(start_rad)
    x2_outer = cx + r_outer * math.cos(end_rad)
    y2_outer = cy + r_outer * math.sin(end_rad)

    # Inner arc points
    x1_inner = cx + r_inner * math.cos(end_rad)
    y1_inner = cy + r_inner * math.sin(end_rad)
    x2_inner = cx + r_inner * math.cos(start_rad)
    y2_inner = cy + r_inner * math.sin(start_rad)

    # Large arc flag (0 for arcs < 180 degrees)
    large_arc = 0

    path = (
        f"M {x1_outer} {y1_outer} "
        f"A {r_outer} {r_outer} 0 {large_arc} 1 {x2_outer} {y2_outer} "
        f"L {x1_inner} {y1_inner} "
        f"A {r_inner} {r_inner} 0 {large_arc} 0 {x2_inner} {y2_inner} "
        f"Z"
    )
    return path


def _rate_to_color(rate: float) -> str:
    """Convert formation rate (0-1) to color."""
    if rate <= 0:
        return "#e8e8e8"  # Gray for no formation
    elif rate < 0.2:
        return "#a8e6cf"  # Light green
    elif rate < 0.4:
        return "#dcedc1"  # Yellow-green
    elif rate < 0.6:
        return "#ffd3a5"  # Light orange
    elif rate < 0.8:
        return "#ffaaa5"  # Salmon
    else:
        return "#ff6b6b"  # Red


def _format_weather_html(weather: dict) -> str:
    """Format weather data as HTML."""
    if not weather:
        return "<p><i>Weather data unavailable</i></p>"

    return f"""
    <div style="background: #f5f5f5; padding: 8px; border-radius: 5px; margin-bottom: 10px;">
        <b>Current Conditions:</b><br>
        <span style="font-size: 12px;">
            Temp: <b>{weather.get('temperature', 'N/A'):.1f}°C</b> |
            Humidity: <b>{weather.get('humidity', 'N/A'):.0f}%</b><br>
            Wind: <b>{weather.get('wind_speed', 'N/A'):.1f} m/s</b> from <b>{weather.get('wind_direction', 'N/A'):.0f}°</b><br>
            Precip: <b>{weather.get('precipitation', 'N/A'):.1f} mm</b> |
            Cloud: <b>{weather.get('cloud_cover', 'N/A'):.0f}%</b>
        </span>
    </div>
    """


def _format_rates_table(rime_rates: dict, verglas_rates: dict) -> str:
    """Format formation rates as an HTML table."""
    rows = []
    for direction in COMPASS_ORDER:
        rime = rime_rates.get(direction, 0)
        verglas = verglas_rates.get(direction, 0)
        rime_color = _rate_to_color(rime)
        verglas_color = _rate_to_color(verglas)

        rows.append(f"""
            <tr>
                <td style="font-weight: bold;">{direction}</td>
                <td style="background: {rime_color}; text-align: center;">{rime:.2f}</td>
                <td style="background: {verglas_color}; text-align: center;">{verglas:.2f}</td>
            </tr>
        """)

    return f"""
    <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
        <tr style="background: #ddd;">
            <th style="padding: 3px;">Aspect</th>
            <th style="padding: 3px;">Rime</th>
            <th style="padding: 3px;">Verglas</th>
        </tr>
        {''.join(rows)}
    </table>
    """


def _add_formation_legend(m: folium.Map) -> None:
    """Add a legend explaining formation rate colors."""
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        z-index: 1000;
        background-color: white;
        padding: 10px;
        border: 2px solid grey;
        border-radius: 5px;
        font-size: 12px;
    ">
        <b>Formation Rate</b><br>
        <i style="background: #ff6b6b; width: 18px; height: 18px; display: inline-block;"></i> 0.8-1.0 (Rapid)<br>
        <i style="background: #ffaaa5; width: 18px; height: 18px; display: inline-block;"></i> 0.6-0.8 (High)<br>
        <i style="background: #ffd3a5; width: 18px; height: 18px; display: inline-block;"></i> 0.4-0.6 (Moderate)<br>
        <i style="background: #dcedc1; width: 18px; height: 18px; display: inline-block;"></i> 0.2-0.4 (Low)<br>
        <i style="background: #a8e6cf; width: 18px; height: 18px; display: inline-block;"></i> 0.0-0.2 (Minimal)<br>
        <i style="background: #e8e8e8; width: 18px; height: 18px; display: inline-block;"></i> None<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


# Keep old functions for backwards compatibility
def create_risk_map(
    risk_data: list[dict],
    weather_data: dict,
    output_path: Optional[str] = None,
) -> str:
    """Create an interactive Folium map showing rime and verglas risk (legacy)."""
    from folium.plugins import HeatMap

    if output_path is None:
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / config.OUTPUT_MAP_FILENAME)

    m = folium.Map(
        location=[config.MAP_CENTER["lat"], config.MAP_CENTER["lon"]],
        zoom_start=config.MAP_ZOOM_START,
        tiles="OpenStreetMap",
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Topographic",
    ).add_to(m)

    rime_layer = folium.FeatureGroup(name="Rime Risk Heatmap")
    verglas_layer = folium.FeatureGroup(name="Verglas Risk Heatmap")

    if risk_data:
        for layer, risk_type in [(rime_layer, "rime"), (verglas_layer, "verglas")]:
            heat_data = []
            for point in risk_data:
                risk = point.get(f"{risk_type}_risk", {})
                score = risk.get("score", 0) if isinstance(risk, dict) else 0
                heat_data.append([point["lat"], point["lon"], score / 100])

            if heat_data:
                HeatMap(heat_data, radius=15, blur=10, max_zoom=10).add_to(layer)

    rime_layer.add_to(m)
    verglas_layer.add_to(m)
    folium.LayerControl().add_to(m)

    m.save(output_path)
    print(f"Map saved to: {output_path}")
    return output_path


def create_simple_map(locations: dict, output_path: Optional[str] = None) -> str:
    """Create a simple map with just location markers."""
    if output_path is None:
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "simple_map.html")

    m = folium.Map(
        location=[config.MAP_CENTER["lat"], config.MAP_CENTER["lon"]],
        zoom_start=config.MAP_ZOOM_START,
        tiles="OpenStreetMap",
    )

    for name, loc in locations.items():
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=f"<b>{name}</b><br>{loc.get('description', '')}",
            tooltip=name,
        ).add_to(m)

    m.save(output_path)
    return output_path


def create_timeseries_map(
    timeseries_data: dict,
    output_path: Optional[str] = None,
) -> str:
    """
    Create an interactive map with time slider and rate/cumulative toggle.

    Args:
        timeseries_data: Dict with structure:
            {
                "timestamps": [list of ISO timestamp strings],
                "locations": {
                    "name": {
                        "altitude": int,
                        "rates": [list of {rime: {}, verglas: {}, weather: {}}]
                    }
                }
            }
        output_path: Where to save the HTML file.

    Returns:
        Path to the generated HTML file.
    """
    import json

    if output_path is None:
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / config.OUTPUT_MAP_FILENAME)

    timestamps = timeseries_data["timestamps"]
    locations = timeseries_data["locations"]

    # Prepare data for JavaScript
    js_data = {
        "timestamps": timestamps,
        "locations": {},
    }

    for name, loc_data in locations.items():
        loc_info = config.FOCUS_AREAS.get(name, {})
        js_data["locations"][name] = {
            "lat": loc_info.get("lat", 0),
            "lon": loc_info.get("lon", 0),
            "altitude": loc_data["altitude"],
            "description": loc_info.get("description", ""),
            "rates": loc_data["rates"],
        }

    # Calculate cumulative totals
    for name, loc in js_data["locations"].items():
        cumulative_rime = {d: 0 for d in COMPASS_ORDER}
        cumulative_verglas = {d: 0 for d in COMPASS_ORDER}
        cumulative_rates = []

        for rates in loc["rates"]:
            for d in COMPASS_ORDER:
                cumulative_rime[d] += rates["rime"].get(d, 0)
                cumulative_verglas[d] += rates["verglas"].get(d, 0)

            cumulative_rates.append({
                "rime": {d: round(cumulative_rime[d], 3) for d in COMPASS_ORDER},
                "verglas": {d: round(cumulative_verglas[d], 3) for d in COMPASS_ORDER},
            })

        loc["cumulative"] = cumulative_rates

    # Generate the HTML with embedded JavaScript
    html_content = _generate_timeseries_html(js_data)

    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"Map saved to: {output_path}")
    return output_path


def _generate_timeseries_html(js_data: dict) -> str:
    """Generate the complete HTML file with embedded map and controls."""
    import json

    data_json = json.dumps(js_data)

    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Rime and Verglas Formation - Scottish Highlands</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 80px; width: 100%; }}
        #controls {{
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 80px;
            background: #fff;
            border-top: 2px solid #ccc;
            padding: 10px 20px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        #slider-row {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        #time-slider {{
            flex-grow: 1;
            height: 20px;
        }}
        #time-display {{
            min-width: 180px;
            font-weight: bold;
            font-size: 14px;
        }}
        #toggle-row {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .toggle-btn {{
            padding: 6px 16px;
            border: 2px solid #2563eb;
            background: white;
            cursor: pointer;
            font-size: 13px;
            border-radius: 4px;
        }}
        .toggle-btn.active {{
            background: #2563eb;
            color: white;
        }}
        #mode-info {{
            color: #666;
            font-size: 12px;
        }}
        .legend {{
            position: absolute;
            bottom: 100px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            border: 2px solid #ccc;
            font-size: 12px;
            z-index: 1000;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin: 3px 0;
        }}
        .legend-color {{
            width: 18px;
            height: 18px;
            display: inline-block;
        }}
        .compass-popup {{
            min-width: 340px;
        }}
        .compass-container {{
            display: flex;
            justify-content: space-around;
            margin: 10px 0;
        }}
        .weather-box {{
            background: #f5f5f5;
            padding: 8px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="controls">
        <div id="slider-row">
            <span>Time:</span>
            <input type="range" id="time-slider" min="0" max="{len(js_data['timestamps'])-1}" value="{len(js_data['timestamps'])-1}" />
            <span id="time-display"></span>
        </div>
        <div id="toggle-row">
            <span>Display:</span>
            <button class="toggle-btn active" id="btn-rate" onclick="setMode('rate')">Rate</button>
            <button class="toggle-btn" id="btn-cumulative" onclick="setMode('cumulative')">Cumulative</button>
            <span id="mode-info">Showing instantaneous formation rate</span>
        </div>
    </div>
    <div class="legend">
        <b>Formation Rate</b><br>
        <div class="legend-item"><span class="legend-color" style="background:#ff6b6b"></span> High</div>
        <div class="legend-item"><span class="legend-color" style="background:#ffd3a5"></span> Moderate</div>
        <div class="legend-item"><span class="legend-color" style="background:#a8e6cf"></span> Low</div>
        <div class="legend-item"><span class="legend-color" style="background:#e8e8e8"></span> None</div>
    </div>

    <script>
        const data = {data_json};
        const compassOrder = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
        let currentMode = 'rate';
        let currentTimeIndex = data.timestamps.length - 1;
        let markers = {{}};

        // Initialize map
        const map = L.map('map').setView([{config.MAP_CENTER["lat"]}, {config.MAP_CENTER["lon"]}], {config.MAP_ZOOM_START});

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Esri'
        }});

        // Color function
        function rateToColor(rate, isCumulative) {{
            if (isCumulative) {{
                // Scale for cumulative (can be > 1)
                const scaled = Math.min(rate / 5, 1);  // 5 = high cumulative
                if (scaled <= 0) return '#e8e8e8';
                if (scaled < 0.2) return '#a8e6cf';
                if (scaled < 0.4) return '#dcedc1';
                if (scaled < 0.6) return '#ffd3a5';
                if (scaled < 0.8) return '#ffaaa5';
                return '#ff6b6b';
            }} else {{
                if (rate <= 0) return '#e8e8e8';
                if (rate < 0.2) return '#a8e6cf';
                if (rate < 0.4) return '#dcedc1';
                if (rate < 0.6) return '#ffd3a5';
                if (rate < 0.8) return '#ffaaa5';
                return '#ff6b6b';
            }}
        }}

        // Create SVG compass
        function createCompassSVG(rates, title, isCumulative) {{
            const size = 120;
            const center = size / 2;
            const outerR = size / 2 - 10;
            const innerR = outerR / 3;

            let segments = '';
            let labels = '';

            compassOrder.forEach((dir, i) => {{
                const rate = rates[dir] || 0;
                const color = rateToColor(rate, isCumulative);
                const startAngle = -90 + i * 45 - 22.5;
                const endAngle = startAngle + 45;

                const path = createArcPath(center, center, innerR, outerR, startAngle, endAngle);
                segments += `<path d="${{path}}" fill="${{color}}" stroke="#333" stroke-width="1"/>`;

                const labelAngle = (startAngle + 22.5) * Math.PI / 180;
                const labelR = outerR + 8;
                const lx = center + labelR * Math.cos(labelAngle);
                const ly = center + labelR * Math.sin(labelAngle);
                labels += `<text x="${{lx}}" y="${{ly}}" text-anchor="middle" dominant-baseline="middle" font-size="9" font-weight="bold">${{dir}}</text>`;
            }});

            return `<svg width="${{size}}" height="${{size + 20}}" xmlns="http://www.w3.org/2000/svg">
                <circle cx="${{center}}" cy="${{center}}" r="${{innerR - 2}}" fill="#f5f5f5" stroke="#333" stroke-width="1"/>
                ${{segments}}
                ${{labels}}
                <text x="${{center}}" y="${{size + 12}}" text-anchor="middle" font-size="11" font-weight="bold">${{title}}</text>
            </svg>`;
        }}

        function createArcPath(cx, cy, rInner, rOuter, startDeg, endDeg) {{
            const startRad = startDeg * Math.PI / 180;
            const endRad = endDeg * Math.PI / 180;

            const x1o = cx + rOuter * Math.cos(startRad);
            const y1o = cy + rOuter * Math.sin(startRad);
            const x2o = cx + rOuter * Math.cos(endRad);
            const y2o = cy + rOuter * Math.sin(endRad);
            const x1i = cx + rInner * Math.cos(endRad);
            const y1i = cy + rInner * Math.sin(endRad);
            const x2i = cx + rInner * Math.cos(startRad);
            const y2i = cy + rInner * Math.sin(startRad);

            return `M ${{x1o}} ${{y1o}} A ${{rOuter}} ${{rOuter}} 0 0 1 ${{x2o}} ${{y2o}} L ${{x1i}} ${{y1i}} A ${{rInner}} ${{rInner}} 0 0 0 ${{x2i}} ${{y2i}} Z`;
        }}

        // Create mini compass for marker icon
        function createMiniCompassSVG(rimeRates, verglasRates, windDir, windSpeed, altitude, isCumulative) {{
            function miniCompass(rates, cx, cy) {{
                let segs = '';
                const r = 14, inner = 4;
                compassOrder.forEach((dir, i) => {{
                    const rate = rates[dir] || 0;
                    const color = rateToColor(rate, isCumulative);
                    const start = -90 + i * 45 - 22.5;
                    const end = start + 45;
                    const path = createArcPath(cx, cy, inner, r, start, end);
                    segs += `<path d="${{path}}" fill="${{color}}" stroke="#333" stroke-width="0.5"/>`;
                }});
                return segs;
            }}

            return `<div style="background:white;border-radius:5px;padding:4px;box-shadow:0 2px 5px rgba(0,0,0,0.3);">
                <svg width="72" height="95" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="18" cy="18" r="3" fill="#eee" stroke="#333" stroke-width="0.5"/>
                    ${{miniCompass(rimeRates, 18, 18)}}
                    <text x="18" y="38" text-anchor="middle" font-size="8" font-weight="bold">Rime</text>
                    <circle cx="54" cy="18" r="3" fill="#eee" stroke="#333" stroke-width="0.5"/>
                    ${{miniCompass(verglasRates, 54, 18)}}
                    <text x="54" y="38" text-anchor="middle" font-size="8" font-weight="bold">Verglas</text>
                    <g transform="translate(36, 58)">
                        <g transform="rotate(${{windDir + 180}})">
                            <line x1="0" y1="7" x2="0" y2="-7" stroke="#2563eb" stroke-width="2"/>
                            <polygon points="0,-9 -3,-4 3,-4" fill="#2563eb"/>
                        </g>
                    </g>
                    <text x="36" y="75" text-anchor="middle" font-size="7" font-weight="bold" fill="#2563eb">${{Math.round(windSpeed)}} mph</text>
                    <text x="36" y="88" text-anchor="middle" font-size="7" font-weight="bold" fill="#666">${{altitude}}m</text>
                </svg>
            </div>`;
        }}

        // Create popup content
        function createPopupContent(name, locData, timeIndex, isCumulative) {{
            const ratesData = isCumulative ? locData.cumulative[timeIndex] : locData.rates[timeIndex];
            const weather = locData.rates[timeIndex].weather;
            const rimeRates = ratesData.rime;
            const verglasRates = ratesData.verglas;

            const rimeSVG = createCompassSVG(rimeRates, 'Rime', isCumulative);
            const verglasSVG = createCompassSVG(verglasRates, 'Verglas', isCumulative);

            let ratesTable = '<table style="width:100%;border-collapse:collapse;font-size:11px;"><tr style="background:#ddd;"><th>Aspect</th><th>Rime</th><th>Verglas</th></tr>';
            compassOrder.forEach(dir => {{
                const r = rimeRates[dir] || 0;
                const v = verglasRates[dir] || 0;
                const rc = rateToColor(r, isCumulative);
                const vc = rateToColor(v, isCumulative);
                ratesTable += `<tr><td style="font-weight:bold">${{dir}}</td><td style="background:${{rc}};text-align:center">${{r.toFixed(2)}}</td><td style="background:${{vc}};text-align:center">${{v.toFixed(2)}}</td></tr>`;
            }});
            ratesTable += '</table>';

            return `<div class="compass-popup">
                <h3 style="margin:0 0 5px 0">${{name}}</h3>
                <p style="margin:0 0 10px 0;color:#666;font-style:italic">${{locData.description}}</p>
                <div class="compass-container">${{rimeSVG}}${{verglasSVG}}</div>
                <div class="weather-box">
                    <b>Conditions at ${{data.timestamps[timeIndex]}}:</b><br>
                    Temp: <b>${{weather.temperature.toFixed(1)}}°C</b> |
                    Humidity: <b>${{weather.humidity.toFixed(0)}}%</b><br>
                    Wind: <b>${{(weather.wind_speed * 2.237).toFixed(0)}} mph</b> from <b>${{weather.wind_direction.toFixed(0)}}°</b><br>
                    Precip: <b>${{weather.precipitation.toFixed(1)}} mm</b>
                </div>
                ${{ratesTable}}
            </div>`;
        }}

        // Update all markers
        function updateMarkers() {{
            const isCumulative = currentMode === 'cumulative';

            Object.keys(data.locations).forEach(name => {{
                const loc = data.locations[name];
                const ratesData = isCumulative ? loc.cumulative[currentTimeIndex] : loc.rates[currentTimeIndex];
                const weather = loc.rates[currentTimeIndex].weather;

                const iconHtml = createMiniCompassSVG(
                    ratesData.rime,
                    ratesData.verglas,
                    weather.wind_direction,
                    weather.wind_speed * 2.237,
                    loc.altitude,
                    isCumulative
                );

                const icon = L.divIcon({{
                    html: iconHtml,
                    iconSize: [80, 105],
                    iconAnchor: [40, 52],
                    className: ''
                }});

                if (markers[name]) {{
                    markers[name].setIcon(icon);
                    markers[name].setPopupContent(createPopupContent(name, loc, currentTimeIndex, isCumulative));
                }} else {{
                    markers[name] = L.marker([loc.lat, loc.lon], {{ icon: icon }})
                        .bindPopup(createPopupContent(name, loc, currentTimeIndex, isCumulative), {{ maxWidth: 400 }})
                        .bindTooltip(name + ' - Click for details')
                        .addTo(map);
                }}
            }});

            // Update time display
            document.getElementById('time-display').textContent = formatTimestamp(data.timestamps[currentTimeIndex]);
        }}

        function formatTimestamp(ts) {{
            const d = new Date(ts);
            return d.toLocaleDateString('en-GB', {{ weekday: 'short', day: 'numeric', month: 'short' }}) +
                   ' ' + d.toLocaleTimeString('en-GB', {{ hour: '2-digit', minute: '2-digit' }});
        }}

        // Mode toggle
        function setMode(mode) {{
            currentMode = mode;
            document.getElementById('btn-rate').classList.toggle('active', mode === 'rate');
            document.getElementById('btn-cumulative').classList.toggle('active', mode === 'cumulative');
            document.getElementById('mode-info').textContent = mode === 'rate'
                ? 'Showing instantaneous formation rate'
                : 'Showing cumulative formation since ' + formatTimestamp(data.timestamps[0]);
            updateMarkers();
        }}

        // Slider event
        document.getElementById('time-slider').addEventListener('input', function(e) {{
            currentTimeIndex = parseInt(e.target.value);
            updateMarkers();
        }});

        // Initialize
        updateMarkers();
    </script>
</body>
</html>'''

    return html
