# Winter climbing conditions dashboard

A Python application to display recent historical winter conditions, and predict rime ice and verglas formation rates on Scottish cliffs using weather data and meteorological rules. Generates interactive maps with compass graphics showing aspect-specific formation rates and historical time series.

<img width="903" height="863" alt="Screenshot 2026-01-21 at 20 50 42" src="https://github.com/user-attachments/assets/9bf6a64b-539d-4489-9d0c-81a778a04ab5" />


## Features

- Fetches historical and forecast weather data from Open-Meteo API (no API key required)
- Calculates rime formation rates for all 8 compass aspects (windward faces accumulate more)
- Calculates verglas formation rates using melt-freeze cycle detection with 24-hour lookback
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

- **Temperature**: Optimal -10°C to -2°C, viable from -15°C to 0°C
- **Humidity**: Requires >85%, higher is better
- **Wind Speed**: More wind increases deposition rate (0-25 m/s scale)
- **Aspect**: Windward faces accumulate fastest, leeward faces still get some (10%)

All factors multiply together - all must be present for significant formation.

### Verglas (0.0-1.0)

Verglas forms when wet surfaces refreeze after a melt period. Uses **melt-freeze cycle detection** with 24-hour lookback:

**Scoring components:**
- **Refreeze Factor** (current conditions): Linear scale from 0°C (no freezing) to -3°C (full refreeze)
- **Melt History Factor** (past 24h): Detects positive temperatures (>0°C) with exponential recency weighting (18-hour half-life)
- **Rainfall During Melt**: Precipitation that occurred during melt periods significantly boosts score

**Formula**: `base_score = refreeze_factor × melt_history_factor`
`verglas_risk = base_score × (0.7 + 0.3 × rain_factor)`

This means dry melt-freeze cycles score up to 0.7, while cycles with 2mm+ rainfall during melt reach 1.0. Verglas is aspect-independent and requires at least 12 hours of historical data.

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
