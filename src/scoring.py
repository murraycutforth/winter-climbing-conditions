"""Risk scoring algorithms for rime ice and verglas formation."""

from typing import Optional

import numpy as np

import config


def calculate_rime_risk(
    temperature: float,
    humidity: float,
    wind_speed: float,
    wind_direction: float,
    elevation: Optional[float] = None,
    aspect: Optional[float] = None,
) -> dict:
    """
    Calculate rime ice formation risk.

    Rime ice forms when supercooled water droplets in fog/cloud freeze on contact
    with cold surfaces. Key factors: sub-zero temps, high humidity, wind exposure.

    Args:
        temperature: Air temperature in °C
        humidity: Relative humidity in %
        wind_speed: Wind speed in m/s
        wind_direction: Wind direction in degrees
        elevation: Elevation in meters (optional)
        aspect: Terrain aspect in degrees (optional)

    Returns:
        Dict with 'score' (0-100), 'level' string, and 'factors' breakdown.
    """
    factors = {}

    # Temperature factor (0-30 points)
    # Optimal: -5 to -10°C, viable: -2 to -15°C
    factors["temperature"] = _score_rime_temperature(temperature)

    # Humidity factor (0-25 points)
    # >85% is ideal, linear scale below
    factors["humidity"] = _score_humidity(humidity)

    # Wind factor (0-20 points)
    # More wind = more rime (brings moisture, deposits droplets)
    factors["wind"] = _score_rime_wind(wind_speed)

    # Elevation factor (0-15 points)
    # Higher = more prone (colder, in cloud more often)
    if elevation is not None:
        factors["elevation"] = _score_elevation(elevation)
    else:
        factors["elevation"] = 7.5  # Neutral score

    # Aspect factor (0-10 points)
    # Windward aspects score higher
    if aspect is not None:
        factors["aspect"] = _score_windward_aspect(aspect, wind_direction)
    else:
        factors["aspect"] = 5.0  # Neutral score

    total_score = sum(factors.values())
    total_score = max(0, min(100, total_score))

    return {
        "score": round(total_score, 1),
        "level": _get_risk_level(total_score),
        "factors": factors,
    }


def calculate_verglas_risk(
    temperature: float,
    humidity: float,
    precipitation: float,
    aspect: Optional[float] = None,
    hour_of_day: Optional[int] = None,
) -> dict:
    """
    Calculate verglas (freezing rain/glaze ice) formation risk.

    Verglas forms when rain falls on surfaces at or below 0°C, or when
    surfaces cool below freezing after being wet. Key factors: near-zero temps,
    recent precipitation, shaded aspects.

    Args:
        temperature: Air temperature in °C
        humidity: Relative humidity in %
        precipitation: Recent precipitation in mm
        aspect: Terrain aspect in degrees (optional)
        hour_of_day: Current hour 0-23 (optional)

    Returns:
        Dict with 'score' (0-100), 'level' string, and 'factors' breakdown.
    """
    factors = {}

    # Temperature factor (0-35 points)
    # Peak around 0°C ±2°C
    factors["temperature"] = _score_verglas_temperature(temperature)

    # Precipitation factor (0-30 points)
    # Recent rain/snow that can freeze
    factors["precipitation"] = _score_precipitation(precipitation)

    # Humidity factor (0-15 points)
    # High humidity helps maintain wet surfaces
    factors["humidity"] = min(15, humidity / 100 * 15)

    # Aspect factor (0-10 points)
    # Shaded (N/NE) aspects retain ice longer
    if aspect is not None:
        factors["aspect"] = _score_shaded_aspect(aspect)
    else:
        factors["aspect"] = 5.0  # Neutral score

    # Time of day factor (0-10 points)
    # Evening/night cooling increases risk
    if hour_of_day is not None:
        factors["time"] = _score_time_of_day(hour_of_day)
    else:
        factors["time"] = 5.0  # Neutral score

    total_score = sum(factors.values())
    total_score = max(0, min(100, total_score))

    return {
        "score": round(total_score, 1),
        "level": _get_risk_level(total_score),
        "factors": factors,
    }


def _score_rime_temperature(temp: float) -> float:
    """Score temperature for rime formation (0-30 points)."""
    if temp > config.RIME_TEMP_VIABLE_MAX or temp < config.RIME_TEMP_VIABLE_MIN:
        return 0

    # Linear ramp up from viable_max to optimal_max
    if temp > config.RIME_TEMP_OPTIMAL_MAX:
        range_size = config.RIME_TEMP_VIABLE_MAX - config.RIME_TEMP_OPTIMAL_MAX
        distance = temp - config.RIME_TEMP_OPTIMAL_MAX
        return 30 * (1 - distance / range_size)

    # Full score in optimal range
    if config.RIME_TEMP_OPTIMAL_MIN <= temp <= config.RIME_TEMP_OPTIMAL_MAX:
        return 30

    # Linear ramp down from optimal_min to viable_min
    range_size = config.RIME_TEMP_OPTIMAL_MIN - config.RIME_TEMP_VIABLE_MIN
    distance = config.RIME_TEMP_OPTIMAL_MIN - temp
    return 30 * (1 - distance / range_size)


def _score_humidity(humidity: float) -> float:
    """Score humidity (0-25 points)."""
    if humidity >= config.RIME_HUMIDITY_THRESHOLD:
        return 25
    # Linear scale below threshold
    return max(0, (humidity / config.RIME_HUMIDITY_THRESHOLD) * 25)


def _score_rime_wind(wind_speed: float) -> float:
    """Score wind for rime formation (0-20 points)."""
    if wind_speed < config.RIME_WIND_MIN:
        # Some points even with light wind
        return (wind_speed / config.RIME_WIND_MIN) * 10

    # More wind = more rime, capped at 20 m/s
    excess_wind = min(wind_speed - config.RIME_WIND_MIN, 15)
    return 10 + (excess_wind / 15) * 10


def _score_elevation(elevation: float) -> float:
    """Score elevation factor (0-15 points)."""
    if elevation < config.ELEVATION_BASE:
        return 0

    elevation_above = elevation - config.ELEVATION_BASE
    score = (elevation_above / config.ELEVATION_SCALE) * 10
    return min(15, score)


def _score_windward_aspect(aspect: float, wind_direction: float) -> float:
    """Score aspect relative to wind direction (0-10 points)."""
    # Windward = facing into the wind (opposite to wind direction)
    windward = (wind_direction + 180) % 360

    # Calculate angular difference
    diff = abs(aspect - windward)
    if diff > 180:
        diff = 360 - diff

    # Full points if facing directly into wind, decreasing with angle
    return max(0, 10 * (1 - diff / 90))


def _score_verglas_temperature(temp: float) -> float:
    """Score temperature for verglas formation (0-35 points)."""
    distance = abs(temp - config.VERGLAS_TEMP_CENTER)

    if distance > config.VERGLAS_TEMP_RANGE * 2:
        return 0

    if distance <= config.VERGLAS_TEMP_RANGE:
        return 35

    # Linear decrease outside optimal range
    excess = distance - config.VERGLAS_TEMP_RANGE
    return 35 * (1 - excess / config.VERGLAS_TEMP_RANGE)


def _score_precipitation(precip: float) -> float:
    """Score recent precipitation (0-30 points)."""
    if precip <= 0:
        return 0

    # Quick ramp up, then diminishing returns
    # 5mm is enough for high risk
    return min(30, precip * 6)


def _score_shaded_aspect(aspect: float) -> float:
    """Score aspect for shade/ice retention (0-10 points)."""
    # N (0°), NE (45°), NW (315°) are shaded
    shaded_center = 0  # North
    diff = abs(aspect - shaded_center)
    if diff > 180:
        diff = 360 - diff

    # Full points for north-facing, decreasing with angle
    # 90° from north gets 0 points
    return max(0, 10 * (1 - diff / 90))


def _score_time_of_day(hour: int) -> float:
    """Score time of day for cooling risk (0-10 points)."""
    # Evening (18-23) and night (0-6) have higher risk
    if 18 <= hour <= 23 or 0 <= hour <= 6:
        return 10
    # Morning (7-9) moderate risk
    if 7 <= hour <= 9:
        return 5
    # Daytime (10-17) lower risk
    return 2


def _get_risk_level(score: float) -> str:
    """Convert numeric score to risk level string."""
    if score >= 75:
        return "extreme"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def get_combined_risk(rime_risk: dict, verglas_risk: dict) -> dict:
    """Combine rime and verglas risks into overall assessment."""
    max_score = max(rime_risk["score"], verglas_risk["score"])

    return {
        "overall_score": round(max_score, 1),
        "overall_level": _get_risk_level(max_score),
        "rime": rime_risk,
        "verglas": verglas_risk,
        "primary_hazard": "rime" if rime_risk["score"] > verglas_risk["score"] else "verglas",
    }


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

    if humidity < 70:  # Need significant moisture
        return 0.0

    # Temperature factor (0-1): optimal at -5 to -10°C
    temp_factor = _score_rime_temperature(temperature) / 30.0

    # Humidity factor (0-1): higher is better
    humidity_factor = min(1.0, (humidity - 70) / 30.0)  # 70-100% maps to 0-1

    # Wind factor (0-1): more wind = faster deposition
    wind_factor = min(1.0, wind_speed / 15.0)  # 0-15 m/s maps to 0-1

    # Aspect factor (0-1): windward faces accumulate fastest
    # Wind direction is where wind comes FROM, so windward aspect faces INTO wind
    windward_aspect = (wind_direction + 180) % 360
    angle_diff = abs(aspect - windward_aspect)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    # Full rate if facing directly into wind, drops to 0.1 at 90° (leeward still gets some)
    aspect_factor = 0.1 + 0.9 * max(0, (90 - angle_diff) / 90)

    # Combine factors - all must be present for significant formation
    base_rate = temp_factor * humidity_factor * wind_factor
    formation_rate = base_rate * aspect_factor

    return round(min(1.0, formation_rate), 3)


def calculate_verglas_formation_rate(
    temperature: float,
    humidity: float,
    precipitation: float,
    aspect: float,
    hour_of_day: Optional[int] = None,
) -> float:
    """
    Calculate verglas formation rate for a specific aspect.

    Formation rate is 0-1 scale. Verglas forms when wet surfaces freeze,
    fastest on shaded aspects near 0°C with recent precipitation.

    Args:
        temperature: Air temperature in °C
        humidity: Relative humidity in %
        precipitation: Recent precipitation in mm
        aspect: Terrain aspect in degrees (0=N, 90=E, 180=S, 270=W)
        hour_of_day: Current hour 0-23 (optional)

    Returns:
        Formation rate from 0 (none) to 1 (maximum).
    """
    # Temperature must be near freezing
    if temperature > 4 or temperature < -4:
        return 0.0

    # Need moisture source (precipitation or high humidity)
    if precipitation <= 0 and humidity < 85:
        return 0.0

    # Temperature factor (0-1): peak at 0°C
    temp_distance = abs(temperature)
    if temp_distance <= 1:
        temp_factor = 1.0
    elif temp_distance <= 4:
        temp_factor = (4 - temp_distance) / 3.0
    else:
        temp_factor = 0.0

    # Moisture factor (0-1)
    if precipitation > 0:
        moisture_factor = min(1.0, precipitation / 3.0)  # 3mm gives full factor
    else:
        moisture_factor = (humidity - 85) / 15.0  # 85-100% maps to 0-1

    # Aspect factor (0-1): shaded (N-facing) aspects retain ice better
    # North = 0°, calculate distance from north
    north_diff = abs(aspect)
    if north_diff > 180:
        north_diff = 360 - north_diff

    # N/NE/NW aspects (within 67.5° of north) get boost
    if north_diff <= 67.5:
        aspect_factor = 1.0 - (north_diff / 135.0)  # 1.0 at N, 0.5 at 67.5°
    else:
        # S-facing aspects still form verglas but melt faster
        aspect_factor = 0.3

    # Time factor: evening/night cooling promotes freezing
    time_factor = 1.0
    if hour_of_day is not None:
        if 10 <= hour_of_day <= 15:  # Midday sun
            time_factor = 0.5
        elif 6 <= hour_of_day <= 9 or 16 <= hour_of_day <= 18:
            time_factor = 0.75

    base_rate = temp_factor * moisture_factor * time_factor
    formation_rate = base_rate * aspect_factor

    return round(min(1.0, formation_rate), 3)


def calculate_aspect_formation_rates(
    temperature: float,
    humidity: float,
    wind_speed: float,
    wind_direction: float,
    precipitation: float,
    hour_of_day: Optional[int] = None,
) -> dict:
    """
    Calculate rime and verglas formation rates for all 8 compass points.

    Args:
        temperature: Air temperature in °C
        humidity: Relative humidity in %
        wind_speed: Wind speed in m/s
        wind_direction: Wind direction in degrees
        precipitation: Recent precipitation in mm
        hour_of_day: Current hour 0-23 (optional)

    Returns:
        Dict with 'rime' and 'verglas' keys, each containing dict of
        compass direction -> formation rate.
    """
    rime_rates = {}
    verglas_rates = {}

    for direction, aspect in COMPASS_POINTS.items():
        rime_rates[direction] = calculate_rime_formation_rate(
            temperature, humidity, wind_speed, wind_direction, aspect
        )
        verglas_rates[direction] = calculate_verglas_formation_rate(
            temperature, humidity, precipitation, aspect, hour_of_day
        )

    return {
        "rime": rime_rates,
        "verglas": verglas_rates,
    }
