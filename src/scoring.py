"""Risk scoring algorithms for rime ice and verglas formation."""

from typing import Optional

import numpy as np

import config


def _rime_temperature_factor(temp: float) -> float:
    """
    Score temperature for rime formation using linear interpolation.

    The scoring function is a trapezoid:
    - Score is 0 below RIME_TEMP_VIABLE_MIN.
    - Ramps up linearly from 0 to 1 between VIABLE_MIN and OPTIMAL_MIN.
    - Score is 1 (optimal) between OPTIMAL_MIN and OPTIMAL_MAX.
    - Ramps down linearly from 1 to 0 between OPTIMAL_MAX and VIABLE_MAX.
    - Score is 0 above RIME_TEMP_VIABLE_MAX.
    """
    # Define the x-coordinates (temperatures) of the trapezoid's corners
    temp_points = [
        config.RIME_TEMP_VIABLE_MIN,
        config.RIME_TEMP_OPTIMAL_MIN,
        config.RIME_TEMP_OPTIMAL_MAX,
        config.RIME_TEMP_VIABLE_MAX,
    ]

    # Define the y-coordinates (scores) corresponding to the temperatures
    score_points = [0, 1, 1, 0]

    # Interpolate the score for the given temperature.
    # np.interp automatically handles cases where `temp` is outside the
    # range of `temp_points`, returning the first or last score (both 0).
    return np.interp(temp, temp_points, score_points)


def _rime_wind_factor(wind_speed: float):
    return min(1.0, wind_speed / config.RIME_WIND_MAX)


def _rime_humidity_factor(humidity: float):
    humidity_factor = (humidity - config.RIME_HUMIDITY_THRESHOLD) / (100.0 - config.RIME_HUMIDITY_THRESHOLD)
    assert humidity_factor <= 1.0
    assert humidity_factor >= 0.0
    return humidity_factor


# Compass directions and their degrees
COMPASS_POINTS = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SW": 225,
    "W": 270,
    "NW": 315,
}


def calculate_rime_formation_rate(
    temperature: float,
    humidity: float,
    wind_speed: float,
    wind_direction: float,
    aspect: float,
) -> float:
    """
    Calculate rime ice formation rate for a specific aspect.

    Formation rate is 0-1 scale representing current ice accumulation rate.
    Rime forms fastest on windward aspects in cold, humid, windy conditions.

    Args:
        temperature: Air temperature in °C
        humidity: Relative humidity in %
        wind_speed: Wind speed in m/s
        wind_direction: Wind direction in degrees (where wind comes FROM)
        aspect: Terrain aspect in degrees (0=N, 90=E, 180=S, 270=W)

    Returns:
        Formation rate from 0 (none) to 1 (maximum).
    """
    # Base conditions must be met for any rime formation
    if temperature > config.RIME_TEMP_VIABLE_MAX or temperature < config.RIME_TEMP_VIABLE_MIN:
        return 0.0

    if humidity < config.RIME_HUMIDITY_THRESHOLD:  # Need significant moisture
        return 0.0

    # Temperature factor (0-1): optimal at -5 to -10°C
    temp_factor = _rime_temperature_factor(temperature)

    # Humidity factor (0-1): higher is better
    humidity_factor = _rime_humidity_factor(humidity)

    # Wind factor (0-1): more wind = faster deposition
    wind_factor = _rime_wind_factor(wind_speed)

    # Aspect factor (0-1): windward faces accumulate fastest
    # Wind direction is where wind comes FROM, so aspect faces INTO wind
    angle_diff = abs(aspect - wind_direction)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    # Full rate if facing directly into wind, drops to 0.1 at 90° (leeward still gets some)
    aspect_factor = 0.1 + 0.9 * max(0, (90 - angle_diff) / 90)

    # Combine factors - all must be present for significant formation
    base_rate = temp_factor * humidity_factor * wind_factor
    formation_rate = base_rate * aspect_factor

    return round(min(1.0, formation_rate), 3)


def _refreeze_temperature_factor(temp: float) -> float:
    """
    Calculate refreeze factor based on current temperature.

    Linear increase from 0°C to -5°C:
    - At 0°C or above: factor = 0 (no freezing)
    - At -5°C or below: factor = 1.0 (full refreeze)
    - Linear interpolation between

    Args:
        temp: Current air temperature in °C

    Returns:
        Refreeze factor from 0 to 1
    """
    if temp >= config.VERGLAS_REFREEZE_TEMP_ZERO:
        return 0.0
    if temp <= config.VERGLAS_REFREEZE_TEMP_FULL:
        return 1.0

    # Linear interpolation between 0°C and min°C
    factor = -temp / abs(config.VERGLAS_REFREEZE_TEMP_FULL)
    return min(1.0, max(0.0, factor))


def _calculate_melt_history_score(past_24h_weather: list) -> float:
    """
    Calculate melt history factor by scanning past 24h for positive temperatures.

    For each hour with temp > 0°C, calculate: recency_weight × intensity
    - Recency weight: exp(-hours_ago / 12) (12-hour half-life)
    - Intensity: min(1.0, temp / 5.0) (normalize 0-5°C)

    Args:
        past_24h_weather: List of weather dicts with 'temperature' key

    Returns:
        Melt history factor from 0 to 1
    """
    if not past_24h_weather:
        return 0.0

    total_score = 0.0

    for hours_ago, weather in enumerate(reversed(past_24h_weather), start=1):
        temp = weather.get("temperature")
        if temp is None:
            continue

        if temp > config.VERGLAS_MELT_TEMP_THRESHOLD:
            # Recency weight: exponential decay with 12-hour half-life
            recency_weight = np.exp(-hours_ago / config.VERGLAS_MELT_RECENCY_HALFLIFE)

            # Intensity: normalize 0-5°C range
            intensity = min(1.0, temp / config.VERGLAS_MELT_TEMP_NORMALIZE)

            total_score += recency_weight * intensity

    # Normalize to 0-1 range
    # Maximum possible score would be if all 24 hours had temp=5°C
    # Sum of exp(-i/12) for i=1 to 24 ≈ 9.5
    # This is too pessimisstic, set empirically to 1
    max_possible_score = 1

    return min(1.0, total_score / max_possible_score)


def _calculate_rainfall_during_melt(past_24h_weather: list) -> float:
    """
    Calculate rainfall factor based on precipitation during melt periods.

    Sum precipitation during hours with temp > 0°C, then normalize.

    Args:
        past_24h_weather: List of weather dicts with 'temperature' and 'precipitation' keys

    Returns:
        Rain factor from 0 to 1
    """
    if not past_24h_weather:
        return 0.0

    total_rainfall = 0.0

    for weather in past_24h_weather:
        temp = weather.get("temperature")
        precip = weather.get("precipitation", 0.0)

        if temp is None or precip is None:
            continue

        if temp > config.VERGLAS_MELT_TEMP_THRESHOLD:
            total_rainfall += precip

    # Normalize: 0mm → 0, 5mm+ → 1.0
    rain_factor = min(1.0, total_rainfall / config.VERGLAS_RAIN_BOOST_NORMALIZE)

    return rain_factor


def calculate_verglas_formation_rate_melt_freeze(
    current_weather: dict,
    past_24h_weather: list,
) -> float:
    """
    Calculate verglas formation rate based on melt-freeze cycles.

    Detects refreeze events (temp ≤ 0°C) following positive temperatures
    in the previous 24 hours, with especially high scores when rainfall
    occurred during the melt period.

    Scoring formula:
        base_score = refreeze_factor × melt_history_factor
        verglas_risk = base_score × (0.7 + 0.3 × rain_factor)

    This ensures:
    - Without rain: max score = base_score × 0.7
    - With 2mm+ rain: max score = base_score × 1.0

    Args:
        current_weather: Dict with keys: temperature, humidity, precipitation, timestamp
        past_24h_weather: List of weather dicts for lookback period

    Returns:
        Formation rate from 0 (none) to 1 (maximum)
    """
    current_temp = current_weather.get("temperature")

    if current_temp is None:
        return 0.0

    # Calculate component factors
    refreeze_factor = _refreeze_temperature_factor(current_temp)

    if refreeze_factor == 0:
        # No freezing occurring, no verglas risk
        return 0.0

    melt_history_factor = _calculate_melt_history_score(past_24h_weather)

    if melt_history_factor == 0:
        # No melt period detected, no melt-freeze risk
        return 0.0

    rain_factor = _calculate_rainfall_during_melt(past_24h_weather)

    # Calculate final score
    base_score = refreeze_factor * melt_history_factor
    verglas_risk = base_score * (0.7 + 0.3 * rain_factor)

    return round(min(1.0, verglas_risk), 3)


def calculate_aspect_formation_rates_with_history(
    current_weather: dict,
    past_24h_weather: list,
) -> dict:
    """
    Calculate rime formation rates for all 8 compass points and verglas rate with melt-freeze detection.

    This function maintains API compatibility by extracting individual values from
    weather dicts and calling the appropriate scoring functions.

    Args:
        current_weather: Dict with keys: temperature, humidity, wind_speed,
                        wind_direction, precipitation, timestamp
        past_24h_weather: List of weather dicts for lookback period

    Returns:
        Dict with 'rime' (dict of compass direction -> rate) and
        'verglas' (single float rate).
    """
    # Extract individual values from current weather
    temperature = current_weather.get("temperature")
    humidity = current_weather.get("humidity")
    wind_speed = current_weather.get("wind_speed")
    wind_direction = current_weather.get("wind_direction")
    precipitation = current_weather.get("precipitation")

    # Calculate rime rates (unchanged - uses current values only)
    rime_rates = {}
    for direction, aspect in COMPASS_POINTS.items():
        rime_rates[direction] = calculate_rime_formation_rate(
            temperature, humidity, wind_speed, wind_direction, aspect
        )

    # Calculate verglas using melt-freeze function if sufficient history
    if len(past_24h_weather) >= config.VERGLAS_MIN_LOOKBACK_HOURS:
        verglas_rate = calculate_verglas_formation_rate_melt_freeze(
            current_weather=current_weather,
            past_24h_weather=past_24h_weather,
        )
    else:
        # Insufficient lookback data - no verglas risk
        verglas_rate = 0.0

    return {
        "rime": rime_rates,
        "verglas": verglas_rate,
    }
