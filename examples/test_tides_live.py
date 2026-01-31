#!/usr/bin/env python3
"""Example script to test tide prediction client.

This demonstrates free, offline tide predictions using harmonic analysis.
No API key required!

Run with: python examples/test_tides_live.py
"""

import asyncio

from nudibranch.clients.tides import TideClient
from nudibranch.config import Config


async def main() -> None:
    """Fetch and display tide predictions for the first dive spot."""
    # Load configuration
    config = Config.load()
    if not config.spots:
        print("No dive spots configured!")
        return

    spot = config.spots[0]
    print(f"Fetching FREE tide predictions for {spot.name} ({spot.lat}, {spot.lng})...")
    print("Using harmonic analysis - no API key required!")
    print("-" * 60)

    client = TideClient()
    tides = await client.fetch_tides(spot.lat, spot.lng, days=3)

    print(f"\nTide Extremes (next 3 days):")
    print(f"Found {len(tides['extremes'])} tide events\n")

    for i, extreme in enumerate(tides["extremes"], 1):
        time_str = extreme["time"].strftime("%Y-%m-%d %H:%M")
        tide_type = extreme["type"]
        height = extreme["height_m"]
        arrow = "↑" if tide_type == "High" else "↓"
        print(f"  {i:2d}. {time_str} - {arrow} {tide_type:4s}: {height:.2f}m")

    print(f"\nHourly Heights (first 12 hours):")
    for i, (time, height) in enumerate(tides["hourly_heights"][:12], 1):
        time_str = time.strftime("%Y-%m-%d %H:%M")
        bar = "█" * int(height * 5)  # Simple bar chart
        print(f"  {time_str}: {height:.2f}m {bar}")

    # Calculate tidal range
    highs = [e["height_m"] for e in tides["extremes"] if e["type"] == "High"]
    lows = [e["height_m"] for e in tides["extremes"] if e["type"] == "Low"]

    print(f"\nTidal Statistics:")
    print(f"  Highest tide: {max(highs):.2f}m")
    print(f"  Lowest tide: {min(lows):.2f}m")
    print(f"  Tidal range: {max(highs) - min(lows):.2f}m")
    print(f"  Mean tide height: {sum(h for _, h in tides['hourly_heights']) / len(tides['hourly_heights']):.2f}m")

    print(f"\nFetched at: {tides['fetched_at']}")
    print("-" * 60)
    print("✓ Completely FREE - no API costs!")
    print("Note: Predictions use simplified harmonic model")
    print("For production use, validate against local tide tables")


if __name__ == "__main__":
    asyncio.run(main())
