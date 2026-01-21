# CLAUDE.md - AI Assistant Context

This file provides context for Claude Code and other AI assistants working on this project.

## Project Overview

Rime and Verglas Predictor: A Python CLI application that predicts rime ice and verglas formation risk on Scottish cliffs using weather data from Open-Meteo API, SRTM terrain data, and meteorological scoring algorithms.

## Key Commands

```bash
# Run full analysis
python main.py

# Run without terrain data (faster, no GDAL required)
python main.py --simple

# Install dependencies
pip install -r requirements.txt

# Required for terrain features
brew install gdal
```

## Architecture

- `main.py` - Entry point, orchestrates all modules
- `config.py` - All configuration constants (bounds, thresholds, colors)
- `src/weather.py` - Open-Meteo API integration with retry logic
- `src/terrain.py` - SRTM DEM loading, aspect/slope calculation
- `src/scoring.py` - Rime and verglas risk algorithms
- `src/visualization.py` - Folium map generation

## Data Flow

1. `main.py` calls `fetch_weather_data()` for focus area conditions
2. `TerrainAnalyzer.load_dem()` downloads/loads SRTM data
3. Grid points generated, terrain queried for each point
4. `calculate_rime_risk()` and `calculate_verglas_risk()` score each point
5. `create_risk_map()` generates interactive HTML map

## Configuration

All tuneable parameters are in `config.py`:
- `FOCUS_AREAS` - Location coordinates
- `SCOTLAND_BOUNDS` - Geographic extent
- Risk thresholds (`RIME_TEMP_OPTIMAL_*`, `VERGLAS_TEMP_*`, etc.)
- Output paths and map styling

## Common Modifications

**Add a new focus area:**
Edit `config.py` FOCUS_AREAS dict with lat, lon, description.

**Adjust risk thresholds:**
Modify constants in `config.py` (e.g., `RIME_TEMP_OPTIMAL_MIN`).

**Change grid resolution:**
Adjust `GRID_SAMPLE_INTERVAL_KM` in `config.py`.

## Dependencies

- `requests` - HTTP for Open-Meteo API
- `numpy`, `pandas` - Data processing
- `rasterio`, `scipy` - Terrain analysis
- `elevation` - SRTM data download (requires GDAL)
- `folium` - Interactive maps

## Known Issues

- DEM download requires GDAL system library
- First run downloads ~50MB of terrain data
- Weather API occasionally rate-limits; retry logic handles this
