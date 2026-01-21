"""Weather data fetching module using Open-Meteo API."""

import time
from datetime import datetime, timedelta
from typing import Optional

import requests

import config

# Open-Meteo historical/archive API
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Hourly parameters for historical data
HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "cloud_cover",
]


def fetch_weather_data(
    locations: Optional[dict] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> dict:
    """
    Fetch weather data from Open-Meteo API for specified locations.

    Args:
        locations: Dict of location names to {"lat": float, "lon": float} dicts.
                  Defaults to config.FOCUS_AREAS.
        max_retries: Number of retry attempts on failure.
        retry_delay: Seconds to wait between retries.

    Returns:
        Dict mapping location names to weather data dicts containing:
        - temperature: Current temperature in °C
        - humidity: Relative humidity in %
        - wind_speed: Wind speed in m/s
        - wind_direction: Wind direction in degrees
        - precipitation: Precipitation in mm
        - cloud_cover: Cloud cover in %
        - timestamp: ISO format timestamp
    """
    if locations is None:
        locations = config.FOCUS_AREAS

    weather_data = {}

    for name, loc in locations.items():
        data = _fetch_location_weather(
            name, loc["lat"], loc["lon"], max_retries, retry_delay
        )
        if data:
            weather_data[name] = data

    return weather_data


def _fetch_location_weather(
    name: str,
    lat: float,
    lon: float,
    max_retries: int,
    retry_delay: float,
) -> Optional[dict]:
    """Fetch weather data for a single location with retries."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(config.WEATHER_PARAMS),
        "wind_speed_unit": "ms",
        "timezone": "Europe/London",
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                config.OPEN_METEO_BASE_URL,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return _parse_weather_response(response.json())

        except requests.RequestException as e:
            print(f"Weather fetch failed for {name} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    print(f"Failed to fetch weather for {name} after {max_retries} attempts")
    return None


def _parse_weather_response(data: dict) -> dict:
    """Parse Open-Meteo API response into standardized format."""
    current = data.get("current", {})

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "precipitation": current.get("precipitation"),
        "cloud_cover": current.get("cloud_cover"),
        "timestamp": current.get("time", datetime.now().isoformat()),
    }


def get_weather_summary(weather_data: dict) -> str:
    """Generate a text summary of weather conditions."""
    lines = ["Current Weather Conditions", "=" * 40]

    for name, data in weather_data.items():
        lines.append(f"\n{name}:")
        lines.append(f"  Temperature: {data['temperature']:.1f}°C")
        lines.append(f"  Humidity: {data['humidity']:.0f}%")
        lines.append(f"  Wind: {data['wind_speed']:.1f} m/s from {data['wind_direction']:.0f}°")
        lines.append(f"  Precipitation: {data['precipitation']:.1f} mm")
        lines.append(f"  Cloud cover: {data['cloud_cover']:.0f}%")

    return "\n".join(lines)


def fetch_historical_weather(
    locations: Optional[dict] = None,
    past_days: int = 7,
    forecast_days: int = 1,
    interval_hours: int = 3,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> dict:
    """
    Fetch historical weather data for the past N days at specified intervals.

    Args:
        locations: Dict of location names to {"lat": float, "lon": float} dicts.
        days: Number of days of history to fetch.
        interval_hours: Interval between data points (e.g., 6 for 6-hourly).
        max_retries: Number of retry attempts on failure.
        retry_delay: Seconds to wait between retries.

    Returns:
        Dict with structure:
        {
            "timestamps": [list of ISO timestamp strings],
            "locations": {
                "location_name": {
                    "altitude": int,
                    "data": [list of weather dicts, one per timestamp]
                }
            }
        }
    """
    if locations is None:
        locations = config.FOCUS_AREAS

    # Calculate date range (archive API has ~5 day delay, so use forecast API for recent data)
    # end_date = datetime.now() + timedelta(days=days_forward)
    # start_date = end_date - timedelta(days=days_back)

    result = {
        "timestamps": [],
        "locations": {},
    }

    # Fetch data for each location
    for name, loc in locations.items():
        print(f"  Fetching historical data for {name}...")
        data = _fetch_location_historical(
            name,
            loc["lat"],
            loc["lon"],
            past_days,
            forecast_days,
            interval_hours,
            max_retries,
            retry_delay,
        )
        if data:
            result["locations"][name] = {
                "altitude": loc.get("altitude", 0),
                "data": data["weather_data"],
            }
            # Use timestamps from first successful fetch
            if not result["timestamps"]:
                result["timestamps"] = data["timestamps"]

    return result


def _fetch_location_historical(
    name: str,
    lat: float,
    lon: float,
    past_days: int,
    forecast_days: int,
    interval_hours: int,
    max_retries: int,
    retry_delay: float,
) -> Optional[dict]:
    """Fetch historical weather data for a single location."""
    # Use the forecast API with past_days for recent history (more reliable)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_PARAMS),
        "past_days": past_days,
        "forecast_days": forecast_days,
        "wind_speed_unit": "ms",
        "timezone": "Europe/London",
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                config.OPEN_METEO_BASE_URL,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return _parse_historical_response(response.json(), interval_hours)

        except requests.RequestException as e:
            print(f"Historical fetch failed for {name} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    print(f"Failed to fetch historical data for {name} after {max_retries} attempts")
    return None


def _parse_historical_response(data: dict, interval_hours: int) -> dict:
    """Parse historical API response and resample to specified interval."""
    hourly = data.get("hourly", {})

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    wind_speed = hourly.get("wind_speed_10m", [])
    wind_dir = hourly.get("wind_direction_10m", [])
    precip = hourly.get("precipitation", [])
    cloud = hourly.get("cloud_cover", [])

    # Resample to interval_hours (take every Nth point)
    timestamps = []
    weather_data = []

    for i in range(0, len(times), interval_hours):
        if i < len(times):
            timestamps.append(times[i])

            # Average values over the interval for smoother data
            end_idx = min(i + interval_hours, len(times))

            def safe_avg(lst, start, end):
                vals = [v for v in lst[start:end] if v is not None]
                return sum(vals) / len(vals) if vals else 0

            def safe_val(lst, idx):
                return lst[idx] if idx < len(lst) and lst[idx] is not None else 0

            weather_data.append({
                "temperature": safe_val(temps, i),
                "humidity": safe_val(humidity, i),
                "wind_speed": safe_val(wind_speed, i),
                "wind_direction": safe_val(wind_dir, i),
                "precipitation": safe_avg(precip, i, end_idx) * interval_hours,  # Sum precip over interval
                "cloud_cover": safe_val(cloud, i),
                "timestamp": times[i],
            })

    return {
        "timestamps": timestamps,
        "weather_data": weather_data,
    }
