#!/usr/bin/env python3
"""Comprehensive demo of the full data aggregation system.

Shows how all components work together to provide complete dive conditions.
Run with: python examples/test_full_aggregator.py
"""

import asyncio

from nudibranch.aggregator import ConditionsAggregator
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient
from nudibranch.config import Config
from nudibranch.safety import SafetyAssessor
from nudibranch.visibility import VisibilityEstimator


async def main() -> None:
    """Demonstrate full conditions aggregation."""
    print("=" * 70)
    print(" NUDIBRANCH - COMPLETE DIVE CONDITIONS DASHBOARD")
    print("=" * 70)

    # Load configuration
    config = Config.load()
    spot = config.spots[0]

    print(f"\n📍 LOCATION: {spot.name}")
    print(f"   Coordinates: {spot.lat}, {spot.lng}")
    print(f"   Region: {spot.region}")
    print(f"   Depth Range: {spot.depth_range}")
    print(f"   {spot.description}")
    print()

    # Initialize all components
    print("Initializing data sources...")
    open_meteo = OpenMeteoClient()
    tide_client = TideClient()
    safety_assessor = SafetyAssessor(config.thresholds)
    visibility_estimator = VisibilityEstimator(config.thresholds)

    aggregator = ConditionsAggregator(
        open_meteo=open_meteo,
        tide_client=tide_client,
        safety_assessor=safety_assessor,
        visibility_estimator=visibility_estimator,
    )

    # Fetch complete conditions
    print("Fetching comprehensive conditions...")
    print()
    conditions = await aggregator.fetch_spot_conditions(spot)

    # Display Marine Conditions
    print("=" * 70)
    print("🌊 MARINE CONDITIONS")
    print("=" * 70)
    if conditions.marine:
        m = conditions.marine
        print(f"  Waves:        {m.wave_height_m:.2f}m @ {m.wave_period_s or 0:.1f}s ({m.wave_direction_deg or 0:.0f}°)")
        print(f"  Swell:        {m.swell_height_m or 0:.2f}m @ {m.swell_period_s or 0:.1f}s")
        print(f"  Wind:         {m.wind_speed_kt:.1f}kt from {m.wind_direction_deg or 0:.0f}°")
        print(f"  Gusts:        {m.wind_gust_kt or 0:.1f}kt")
        print(f"  Temperature:  {m.temperature_c or 0:.1f}°C")
        print(f"  Cloud Cover:  {m.cloud_cover_pct or 0}%")
        print(f"  Beaufort:     Force {conditions.metadata.get('wind_speed_beaufort', 0)}")
    print()

    # Display Tide Information
    print("=" * 70)
    print("🌙 TIDE INFORMATION")
    print("=" * 70)
    if conditions.tides:
        t = conditions.tides
        arrow = "↑ RISING" if t.is_rising else "↓ FALLING"
        print(f"  Current:      {t.current_height_m or 0:.2f}m {arrow}")

        if t.next_high:
            time_diff = (t.next_high.time - conditions.fetched_at).total_seconds() / 3600
            print(f"  Next High:    {t.next_high.time.strftime('%H:%M')} ({t.next_high.height_m:.2f}m) in {time_diff:.1f}h")

        if t.next_low:
            time_diff = (t.next_low.time - conditions.fetched_at).total_seconds() / 3600
            print(f"  Next Low:     {t.next_low.time.strftime('%H:%M')} ({t.next_low.height_m:.2f}m) in {time_diff:.1f}h")

        print(f"\n  Upcoming Tides (next 24h):")
        for extreme in t.extremes[:6]:
            if extreme.time > conditions.fetched_at:
                icon = "↑" if extreme.type == "High" else "↓"
                print(f"    {icon} {extreme.time.strftime('%a %H:%M')} - {extreme.type:4s}: {extreme.height_m:.2f}m")
    print()

    # Display Safety Assessment
    print("=" * 70)
    print("⚠️  SAFETY ASSESSMENT")
    print("=" * 70)
    if conditions.safety:
        # Safety is a SafetyAssessment Pydantic model
        s = conditions.safety
        status_colors = {
            "safe": "✅ SAFE",
            "caution": "⚠️  CAUTION",
            "unsafe": "❌ UNSAFE"
        }
        print(f"  Overall: {status_colors.get(s.overall.value, s.overall.value.upper())}")

        if s.limiting_factor:
            print(f"  Limiting Factor: {s.limiting_factor.upper()}")

        print(f"\n  Factor Breakdown:")
        for name, factor in s.factors.items():
            status_sym = {"safe": "✓", "caution": "~", "unsafe": "✗"}
            sym = status_sym.get(factor["status"].value, "?")
            print(f"    {sym} {name.capitalize():12s} {factor['value']:.1f}{factor['unit']:3s} - {factor['status'].value.upper()}")
    print()

    # Display Visibility Estimate
    print("=" * 70)
    print("👁️  VISIBILITY ESTIMATE")
    print("=" * 70)
    if conditions.visibility:
        # Visibility is a VisibilityEstimate Pydantic model
        v = conditions.visibility
        vis_icons = {
            "good": "✅ GOOD",
            "mixed": "⚠️  MIXED",
            "poor": "❌ POOR"
        }
        print(f"  Level:        {vis_icons.get(v.level.value, v.level.value.upper())} ({v.range_estimate})")
        print(f"  Confidence:   {v.confidence.upper()}")

        print(f"\n  Contributing Factors:")
        status_sym = {"favorable": "✓", "moderate": "~", "unfavorable": "✗"}
        for name, indicator in v.indicators.items():
            sym = status_sym.get(indicator["status"], "?")
            print(f"    {sym} {name.capitalize():10s} - {indicator['message']}")

        print(f"\n  Notes: {v.notes}")
    print()

    # Display Metadata
    print("=" * 70)
    print("ℹ️  SYSTEM STATUS")
    print("=" * 70)
    print(f"  Data Sources:")
    for source, status in conditions.metadata["cache_status"].items():
        status_icon = "✓" if status == "fetched" else "✗"
        print(f"    {status_icon} {source.capitalize():12s} {status}")

    if "errors" in conditions.metadata and conditions.metadata["errors"]:
        print(f"\n  Errors:")
        for source, error in conditions.metadata["errors"].items():
            print(f"    ✗ {source}: {error}")

    print(f"\n  Fetched: {conditions.fetched_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("=" * 70)
    print("Dashboard ready! All data successfully aggregated.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
