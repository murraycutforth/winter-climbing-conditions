"""Configuration constants for the Rime and Verglas Predictor."""

# Geographic bounds for Scotland (focus area)
SCOTLAND_BOUNDS = {
    "north": 58.0,
    "south": 56.0,
    "east": -3.0,
    "west": -6.0,
}

# Focus areas with coordinates (lat, lon) and summit altitude (m)
FOCUS_AREAS = {
    "Carn Etchachan": {"lat": 57.090306, "lon": -3.646159, "altitude": 1120, "description": "Summit of Carn Etchachan"},
    "Ben Nevis": {"lat": 56.798691, "lon": -5.014505, "altitude": 1150, "description": "Number 3 gully buttress"},
    # "Glencoe": {"lat": 56.682, "lon": -4.985, "altitude": 1150, "description": "Buachaille Etive Mor and Aonach Eagach"},
    "Creag Meagaidh": {"lat": 56.955834, "lon": -4.580079, "altitude": 850, "description": "Coire Ardair cliffs"},
    "Lochnagar": {"lat": 56.957672, "lon": -3.241534, "altitude": 1000, "description": "Black spout wall"},
    "Beinn Eighe": {"lat": 57.584998, "lon": -5.431174, "altitude": 850, "description": "Far east wall"},
    # "Beinn Bhan": {"lat": 57.42, "lon": -5.68, "altitude": 896, "description": "Applecross corries"},
}

# Open-Meteo API configuration
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "cloud_cover",
]

# DEM configuration
DEM_CACHE_DIR = "data/dem"
DEM_RESOLUTION_M = 90  # SRTM 90m resolution
GRID_SAMPLE_INTERVAL_KM = 1.0  # Sample terrain every 1km for visualization

# Risk scoring thresholds
RIME_TEMP_OPTIMAL_MIN = -10  # °C
RIME_TEMP_OPTIMAL_MAX = -2   # °C
RIME_TEMP_VIABLE_MIN = -15   # °C
RIME_TEMP_VIABLE_MAX = 0    # °C
RIME_HUMIDITY_THRESHOLD = 85  # %
RIME_WIND_MAX = 25  # m/s (10 m/s = 22mph)

VERGLAS_TEMP_CENTER = 0  # °C
VERGLAS_TEMP_RANGE = 2   # ±°C

# Melt-freeze cycle detection for verglas
VERGLAS_LOOKBACK_HOURS = 24
VERGLAS_MELT_TEMP_THRESHOLD = 0.0  # °C (more generous - count temps at/above freezing)
VERGLAS_MELT_RECENCY_HALFLIFE = 18  # hours (longer memory - older melt periods count more)
VERGLAS_MELT_TEMP_NORMALIZE = 5.0  # °C
VERGLAS_RAIN_BOOST_NORMALIZE = 2.0  # mm
VERGLAS_MIN_LOOKBACK_HOURS = 12

# Refreeze temperature scoring
VERGLAS_REFREEZE_TEMP_ZERO = 0     # °C - no freezing above this
VERGLAS_REFREEZE_TEMP_FULL = -3    # °C - full refreeze factor at/below this (more optimistic)

# Elevation factors
ELEVATION_BASE = 800  # meters, baseline for elevation scoring
ELEVATION_SCALE = 400  # meters per 10 points

# Aspect weights (0-360 degrees, 0=N, 90=E, 180=S, 270=W)
# Windward aspects for prevailing westerlies
WINDWARD_ASPECTS = [225, 270, 315]  # SW, W, NW
SHADED_ASPECTS = [0, 45, 315]  # N, NE, NW

# Output configuration
OUTPUT_DIR = "output"
OUTPUT_MAP_FILENAME = "risk_map.html"

# Map visualization
MAP_CENTER = {"lat": 56.9, "lon": -4.5}
MAP_ZOOM_START = 8
RISK_COLORS = {
    "low": "#2ecc71",      # Green
    "moderate": "#f1c40f",  # Yellow
    "high": "#e67e22",      # Orange
    "extreme": "#e74c3c",   # Red
}
