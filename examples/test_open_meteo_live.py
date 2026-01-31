#!/usr/bin/env python3
"""Example script to test Open-Meteo client with live API calls.

This demonstrates fetching real marine and weather conditions for a Phuket dive spot.
Run with: python examples/test_open_meteo_live.py
"""

import asyncio

from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.config import Config


async def main() -> None:
    """Fetch and display conditions for the first dive spot."""
    # Load configuration
    config = Config.load()
    if not config.spots:
        print("No dive spots configured!")
        return

    spot = config.spots[0]
    print(f"Fetching conditions for {spot.name} ({spot.lat}, {spot.lng})...")
    print("-" * 60)

    async with OpenMeteoClient() as client:
        # Fetch marine conditions
        print("\nMarine Conditions:")
        try:
            marine = await client.fetch_marine(spot.lat, spot.lng)
            print(f"  Wave Height: {marine['wave_height_m']:.1f}m")
            print(f"  Wave Period: {marine['wave_period_s']:.1f}s" if marine['wave_period_s'] else "  Wave Period: N/A")
            print(f"  Wave Direction: {marine['wave_direction_deg']:.0f}°" if marine['wave_direction_deg'] else "  Wave Direction: N/A")
            print(f"  Swell Height: {marine['swell_height_m']:.1f}m" if marine['swell_height_m'] else "  Swell Height: N/A")
            print(f"  Swell Period: {marine['swell_period_s']:.1f}s" if marine['swell_period_s'] else "  Swell Period: N/A")
        except Exception as e:
            print(f"  Error: {e}")

        # Fetch weather conditions
        print("\nWeather Conditions:")
        try:
            weather = await client.fetch_weather(spot.lat, spot.lng)
            print(f"  Wind Speed: {weather['wind_speed_kt']:.1f}kt")
            print(f"  Wind Direction: {weather['wind_direction_deg']:.0f}°" if weather['wind_direction_deg'] else "  Wind Direction: N/A")
            print(f"  Wind Gust: {weather['wind_gust_kt']:.1f}kt" if weather['wind_gust_kt'] else "  Wind Gust: N/A")
            print(f"  Temperature: {weather['temperature_c']:.1f}°C" if weather['temperature_c'] else "  Temperature: N/A")
            print(f"  Precipitation: {weather['precipitation_mm']:.1f}mm")
            print(f"  Cloud Cover: {weather['cloud_cover_pct']}%")
        except Exception as e:
            print(f"  Error: {e}")

        # Fetch combined data
        print("\nCombined Data (single call):")
        try:
            combined = await client.fetch_combined(spot.lat, spot.lng)
            print(f"  All metrics fetched successfully")
            print(f"  Timestamp: {combined['timestamp']}")
        except Exception as e:
            print(f"  Error: {e}")

    print("-" * 60)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
