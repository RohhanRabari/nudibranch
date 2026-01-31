#!/usr/bin/env python3
"""Example demonstrating visibility estimation system.

Shows how underwater visibility is estimated from proxy indicators.
Run with: python examples/test_visibility_estimation.py
"""

import asyncio

from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.config import Config
from nudibranch.visibility import VisibilityEstimator


async def main() -> None:
    """Demonstrate visibility estimation with live data."""
    print("Underwater Visibility Estimation Demo")
    print("=" * 60)

    # Load configuration
    config = Config.load()
    spot = config.spots[0]

    print(f"\nEstimating visibility for: {spot.name}")
    print(f"Location: {spot.lat}, {spot.lng}")
    print()

    # Fetch live conditions
    print("Fetching current conditions...")
    async with OpenMeteoClient() as client:
        marine = await client.fetch_marine(spot.lat, spot.lng)
        weather = await client.fetch_weather(spot.lat, spot.lng)

    # For demo, simulate 3-day and 5-day averages
    # In production, you'd calculate these from historical data
    recent_rainfall = weather["precipitation_mm"] * 3  # Rough estimate
    avg_wind_speed = weather["wind_speed_kt"]  # Current as proxy for average

    print("Proxy Indicators:")
    print(f"  Satellite turbidity: Not available (demo)")
    print(f"  Recent rainfall (3d): ~{recent_rainfall:.1f}mm (estimated)")
    print(f"  Avg wind speed (5d): ~{avg_wind_speed:.1f}kt (current as proxy)")
    print(f"  Current swell: {marine['swell_height_m']:.2f}m")
    print()

    # Create estimator
    estimator = VisibilityEstimator(config.thresholds)

    # Estimate visibility
    estimate = estimator.estimate_visibility(
        turbidity_fnu=None,  # No satellite data in demo
        recent_rainfall_mm=recent_rainfall,
        avg_wind_speed_kt=avg_wind_speed,
        swell_height_m=marine["swell_height_m"],
    )

    # Display results
    print("=" * 60)
    print(f"ESTIMATED VISIBILITY: {estimate['level'].value.upper()}")
    print(f"Range: {estimate['range_estimate']}")
    print(f"Confidence: {estimate['confidence'].upper()}")
    print("=" * 60)
    print()

    # Show indicator breakdown
    print("Contributing Factors:")
    status_symbols = {"favorable": "✓", "moderate": "~", "unfavorable": "✗"}

    for name, indicator in estimate["indicators"].items():
        symbol = status_symbols.get(indicator["status"], "?")
        status_str = indicator["status"].upper()
        value_str = f"{indicator['value']:.1f}"

        print(f"  {symbol} {name.capitalize():10s} {value_str:8s} - {status_str}")
        print(f"     {indicator['message']}")

    print()
    print("Notes:")
    for line in estimate["notes"].split(". "):
        if line.strip():
            print(f"  • {line.strip()}")

    print()
    print("=" * 60)
    print("Visibility Guide:")
    print("  GOOD (>20m):  Can see clearly, excellent conditions")
    print("  MIXED (10-20m): Moderate visibility, acceptable for diving")
    print("  POOR (<10m):  Limited visibility, challenging conditions")
    print()
    print("⚠️  IMPORTANT:")
    print("  This is an ESTIMATE based on weather/sea state proxies.")
    print("  For actual visibility, check:")
    print("  - Local dive shop reports")
    print("  - Recent diver observations")
    print("  - Live camera feeds if available")
    print()
    print("  Satellite turbidity data (when available) improves accuracy.")


if __name__ == "__main__":
    asyncio.run(main())
