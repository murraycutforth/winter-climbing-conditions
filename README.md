# Rime and Verglas Formation Predictor

A Python application to predict rime ice and verglas formation rates on Scottish cliffs using weather data and meteorological rules. Generates interactive maps with compass graphics showing aspect-specific formation rates and historical time series.

## Features

- Fetches historical and forecast weather data from Open-Meteo API (no API key required)
- Calculates rime formation rates for all 8 compass aspects (windward faces accumulate more)
- Calculates verglas formation rates based on temperature and precipitation
- Generates interactive HTML map with:
  - Time slider to view conditions over past days and forecast
  - Compass graphics showing rime rates by aspect
  - Wind direction and speed indicators
  - Temperature and altitude display
  - Click popups with weather time series charts

## Focus Areas

- **Carn Etchachan** - Cairngorms plateau (1120m)
- **Ben Nevis** - North face and CMD arrete (1150m)
- **Creag Meagaidh** - Coire Ardair cliffs (850m)
- **Lochnagar** - Cairngorms (1000m)
- **Beinn Eighe** - Torridon (850m)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Options:
- `--output PATH` - Custom output path for the HTML map file

### Output

The application generates:

1. Console output with current weather conditions and formation rates
2. An interactive HTML map at `output/formation_map.html`

Open the HTML file in a web browser to view:
- Time slider to browse historical and forecast conditions
- Compass graphics at each location showing aspect-specific rime rates
- Verglas rate indicator
- Click any marker to see temperature, wind, and precipitation time series

## Formation Rate Scoring

### Rime Ice (0.0-1.0)

Rime forms when supercooled water droplets freeze on contact with cold surfaces. Formation rate depends on:

- **Temperature**: Optimal -5C to -10C, viable from -2C to -15C
- **Humidity**: Requires >70%, higher is better
- **Wind Speed**: More wind increases deposition rate (0-15 m/s scale)
- **Aspect**: Windward faces accumulate fastest, leeward faces still get some (10%)

All factors multiply together - all must be present for significant formation.

### Verglas (0.0-1.0)

Verglas forms when rain freezes on surfaces at or below 0C. Formation rate depends on:

- **Temperature**: Peak around 0C, viable -4C to +4C
- **Moisture**: Requires recent precipitation OR humidity >85%
- **Time of Day**: Evening/night cooling promotes freezing, midday sun reduces it

Verglas is aspect-independent - it forms equally on all faces.

## Project Structure

```
rime-predictor/
├── src/
│   ├── __init__.py       # Package exports
│   ├── weather.py        # Open-Meteo API integration
│   ├── scoring.py        # Formation rate algorithms
│   └── visualization.py  # Interactive map generation
├── main.py               # CLI entry point
├── config.py             # Configuration constants
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Limitations

- Weather data from Open-Meteo forecast API with past_days parameter (not true reanalysis)
- Formation models are heuristic approximations based on meteorological principles
- Real-time conditions at specific cliff faces may vary from summit weather data

## License

MIT
