#!/usr/bin/env python3
"""Example demonstrating safety assessment system.

Shows how conditions are evaluated against thresholds.
Run with: python examples/test_safety_assessment.py
"""

import asyncio

from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.config import Config
from nudibranch.safety import SafetyAssessor


async def main() -> None:
    """Demonstrate safety assessment with live data."""
    print("Safety Assessment Demo")
    print("=" * 60)

    # Load configuration
    config = Config.load()
    spot = config.spots[0]

    print(f"\nAssessing conditions for: {spot.name}")
    print(f"Location: {spot.lat}, {spot.lng}")
    print()

    # Fetch live marine conditions
    print("Fetching current conditions...")
    async with OpenMeteoClient() as client:
        marine = await client.fetch_marine(spot.lat, spot.lng)
        weather = await client.fetch_weather(spot.lat, spot.lng)

    conditions = {
        "wind_speed_kt": weather["wind_speed_kt"],
        "wave_height_m": marine["wave_height_m"],
        "swell_height_m": marine["swell_height_m"],
        "swell_period_s": marine["swell_period_s"],
        "wind_gust_kt": weather["wind_gust_kt"],
    }

    print("Current Conditions:")
    print(f"  Wind: {conditions['wind_speed_kt']:.1f} kt")
    print(f"  Waves: {conditions['wave_height_m']:.2f} m")
    print(f"  Swell: {conditions['swell_height_m']:.2f} m @ {conditions['swell_period_s']:.1f}s")
    print(f"  Gusts: {conditions['wind_gust_kt']:.1f} kt")
    print()

    # Create assessor with config thresholds
    assessor = SafetyAssessor(config.thresholds)

    # Assess conditions
    assessment = assessor.assess_conditions(conditions)

    # Display results
    print("=" * 60)
    print(f"OVERALL SAFETY: {assessment['overall'].value.upper()}")
    print("=" * 60)
    print()

    # Color coding for terminal
    status_symbols = {
        "safe": "✓",
        "caution": "⚠",
        "unsafe": "✗"
    }

    print("Individual Factors:")
    for name, factor in assessment["factors"].items():
        symbol = status_symbols.get(factor["status"].value, "?")
        status_str = factor["status"].value.upper()
        value_str = f"{factor['value']:.1f}{factor['unit']}"

        print(f"  {symbol} {name.capitalize():12s} {value_str:10s} - {status_str}")
        print(f"     {factor['message']}")

    print()
    if assessment["limiting_factor"]:
        print(f"Limiting Factor: {assessment['limiting_factor'].upper()}")
        print()

    print("Details:")
    print(f"  {assessment['details']}")
    print()

    # Show thresholds used
    print("=" * 60)
    print("Configured Safety Thresholds:")
    print()
    threshold_names = {
        "wind_speed_kt": "Wind Speed",
        "wave_height_m": "Wave Height",
        "swell_height_m": "Swell Height",
        "swell_period_s": "Swell Period",
        "wind_gust_kt": "Wind Gusts",
    }

    for key, name in threshold_names.items():
        if key in config.thresholds:
            t = config.thresholds[key]
            print(f"  {name:15s}: Safe ≤{t['safe']:4.1f}  |  Caution ≤{t['caution']:4.1f}  |  Unsafe >{t['caution']:4.1f}")

    print()
    print("=" * 60)
    print("Note: Thresholds can be customized in config/thresholds.yaml")


if __name__ == "__main__":
    asyncio.run(main())
