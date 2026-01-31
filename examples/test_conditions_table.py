#!/usr/bin/env python3
"""Demo of the conditions table widget with live data.

Shows the table fetching and displaying real conditions for all dive spots.
Run with: python examples/test_conditions_table.py

The table will:
- Start with "Loading..." placeholders
- Fetch actual conditions from APIs
- Update rows with real data
- Color-code safety status (green/yellow/red)
- Format waves, wind, swell, tides, visibility

Press 'r' to refresh data
Press 'q' to quit
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - CONDITIONS TABLE DEMO")
    print("=" * 70)
    print()
    print("This demo shows the conditions table with LIVE DATA from:")
    print("  • Open-Meteo Marine API (waves, wind, swell, weather)")
    print("  • Harmonic tide predictions (high/low times)")
    print("  • Safety assessment (SAFE/CAUTION/UNSAFE)")
    print("  • Visibility estimation (GOOD/MIXED/POOR)")
    print()
    print("Features:")
    print("  ✓ Color-coded status indicators")
    print("  ✓ Formatted marine conditions (waves, wind, swell)")
    print("  ✓ Tide direction and next event")
    print("  ✓ Real-time data refresh")
    print()
    print("Key Bindings:")
    print("  r - Refresh all conditions")
    print("  q - Quit")
    print()
    print("=" * 70)
    print("Loading dive spots...")
    print()
    print("Press ENTER to launch the dashboard...")
    input()

    main()
