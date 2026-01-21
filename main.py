#!/usr/bin/env python3
"""
Rime and Verglas Predictor - Main Entry Point

Predicts rime ice and verglas formation rates on Scottish cliffs using
weather data and meteorological rules. Shows aspect-specific rates on
compass graphics for each location with historical time series.
"""

import argparse
from datetime import datetime

import config
from src.weather import fetch_historical_weather
from src.scoring import calculate_aspect_formation_rates
from src.visualization import create_timeseries_map


def main():
    """Main entry point for the rime predictor."""
    args = parse_args()

    print("=" * 60)
    print("Rime and Verglas Formation Rate Predictor")
    print("Scottish Highlands - Climbing Conditions")
    print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Fetch historical weather data
    print("\n[1/3] Fetching 7-day historical weather data (3-hourly)...")
    historical_data = fetch_historical_weather(
        days=7,
        interval_hours=3,
    )

    if not historical_data["locations"]:
        print("ERROR: Failed to fetch weather data. Check internet connection.")
        return 1

    timestamps = historical_data["timestamps"]
    print(f"  Retrieved {len(timestamps)} time points from {timestamps[0]} to {timestamps[-1]}")

    # Calculate formation rates for all time points and locations
    print("\n[2/3] Calculating formation rates for all time points...")

    timeseries_data = {
        "timestamps": timestamps,
        "locations": {},
    }

    for name, loc_data in historical_data["locations"].items():
        altitude = loc_data["altitude"]
        weather_series = loc_data["data"]

        print(f"  Processing {name}...")

        location_rates = []
        for i, weather in enumerate(weather_series):
            # Parse hour from timestamp for time-of-day factor
            try:
                hour = int(weather["timestamp"].split("T")[1].split(":")[0])
            except (IndexError, ValueError):
                hour = 12

            rates = calculate_aspect_formation_rates(
                temperature=weather["temperature"],
                humidity=weather["humidity"],
                wind_speed=weather["wind_speed"],
                wind_direction=weather["wind_direction"],
                precipitation=weather["precipitation"],
                hour_of_day=hour,
            )

            # Add weather info to rates for display
            rates["weather"] = weather
            location_rates.append(rates)

        timeseries_data["locations"][name] = {
            "altitude": altitude,
            "rates": location_rates,
        }

    # Print summary for most recent time point
    print("\n" + "=" * 60)
    print(f"LATEST CONDITIONS ({timestamps[-1]})")
    print("=" * 60)

    for name, loc_data in timeseries_data["locations"].items():
        latest = loc_data["rates"][-1]
        weather = latest["weather"]
        rime_rates = latest["rime"]
        verglas_rates = latest["verglas"]

        max_rime = max(rime_rates.values())
        max_verglas = max(verglas_rates.values())

        print(f"\n{name} ({loc_data['altitude']}m):")
        print(f"  {weather['temperature']:.1f}°C, {weather['wind_speed']*2.237:.0f} mph wind")

        if max_rime > 0:
            max_aspects = [d for d, r in rime_rates.items() if r == max_rime]
            print(f"  Rime: {max_rime:.2f} on {', '.join(max_aspects)}")
        else:
            print(f"  Rime: None")

        if max_verglas > 0:
            max_aspects = [d for d, r in verglas_rates.items() if r == max_verglas]
            print(f"  Verglas: {max_verglas:.2f} on {', '.join(max_aspects)}")
        else:
            print(f"  Verglas: None")

    # Generate interactive map
    print("\n[3/3] Generating interactive time series map...")
    output_path = create_timeseries_map(timeseries_data, args.output)

    print(f"\nMap saved to: {output_path}")
    print("\nFeatures:")
    print("  - Use the slider to view conditions at different times over the past week")
    print("  - Toggle between 'Rate' (instantaneous) and 'Cumulative' (total over time)")
    print("  - Click markers for detailed information")

    return 0


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Predict rime and verglas formation rates on Scottish cliffs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for the formation rate map HTML file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    exit(main())
