# Rime and Verglas Predictor

A Python application to predict rime ice and verglas formation risk on Scottish cliffs using weather data, terrain analysis, and meteorological rules.

## Features

- Fetches real-time weather data from Open-Meteo API (no API key required)
- Downloads and processes SRTM digital elevation model data
- Calculates terrain aspect and slope for risk assessment
- Scores rime and verglas risk using meteorological rules
- Generates interactive Folium maps with heatmaps and markers

## Focus Areas

- **Cairngorms** - Cairngorm plateau and Northern Corries
- **Ben Nevis** - North face and CMD arête
- **Glencoe** - Buachaille Etive Mor and Aonach Eagach
- **Creag Meagaidh** - Coire Ardair cliffs

## Installation

### Prerequisites

For full terrain analysis, install GDAL:

```bash
brew install gdal
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Full Analysis (with terrain data)

```bash
python main.py
```

On first run, the application will download SRTM elevation data for Scotland (~56-58°N). This requires an internet connection and may take a few minutes.

### Simplified Analysis (weather only)

```bash
python main.py --simple
```

This mode skips terrain analysis and provides risk assessment based on weather data alone.

### Output

The application generates:

1. Console output with weather conditions and risk scores
2. An interactive HTML map at `output/risk_map.html`

Open the HTML file in a web browser to view:
- Risk heatmaps (toggle between rime and verglas layers)
- Location markers with detailed conditions
- Topographic base map option

## Risk Scoring

### Rime Ice (0-100)

Rime forms when supercooled water droplets freeze on contact with cold surfaces.

Factors:
- **Temperature** (30 pts): Optimal -5°C to -10°C
- **Humidity** (25 pts): >85% ideal
- **Wind** (20 pts): Higher wind = more rime deposition
- **Elevation** (15 pts): Higher = more prone
- **Aspect** (10 pts): Windward faces score higher

### Verglas (0-100)

Verglas forms when rain freezes on surfaces at or below 0°C.

Factors:
- **Temperature** (35 pts): Peak around 0°C ±2°C
- **Precipitation** (30 pts): Recent rain/snow
- **Humidity** (15 pts): Maintains wet surfaces
- **Aspect** (10 pts): North-facing retains ice
- **Time** (10 pts): Evening/night cooling

### Risk Levels

- **Extreme** (75-100): Very hazardous conditions
- **High** (50-75): Significant ice likely
- **Moderate** (25-50): Some ice formation possible
- **Low** (0-25): Minimal risk

## Project Structure

```
rime-predictor/
├── src/
│   ├── __init__.py       # Package exports
│   ├── weather.py        # Open-Meteo API integration
│   ├── terrain.py        # DEM processing and analysis
│   ├── scoring.py        # Risk calculation algorithms
│   └── visualization.py  # Folium map generation
├── main.py               # CLI entry point
├── config.py             # Configuration constants
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── CLAUDE.md             # AI assistant context
```

## Limitations

- Weather data is point-based; interpolation between stations is simplified
- SRTM data is 90m resolution; micro-terrain features not captured
- Risk models are heuristic approximations, not validated predictions
- Real-time conditions may vary significantly from forecasts

## License

MIT
