#!/usr/bin/env python3
"""Demo of the tide panel widget with live data.

Shows detailed tide information for selected dive spots.
Run with: python examples/test_tide_panel.py

The tide panel displays:
- Current tide height and direction (rising/falling)
- Next high and low tide times with heights
- Time remaining until next events
- ASCII tide curve chart for 24 hours
- Upcoming tide extremes list

Navigation:
- Use arrow keys to select different dive spots in the table
- The tide panel updates automatically when you select a spot
- Press 'q' to quit
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - TIDE PANEL DEMO")
    print("=" * 70)
    print()
    print("This demo shows detailed tide information:")
    print()
    print("CURRENT TIDE")
    print("  • Current height (e.g., 1.54m)")
    print("  • Direction: ↑ RISING or ↓ FALLING")
    print()
    print("NEXT EVENTS")
    print("  • Next high tide time, height, and time remaining")
    print("  • Next low tide time, height, and time remaining")
    print()
    print("TIDE CURVE")
    print("  • ASCII chart showing tide pattern for next 24 hours")
    print("  • Visual representation of high (▲) and low (▼) tides")
    print()
    print("UPCOMING TIDES")
    print("  • List of next 6 tide extremes")
    print("  • Color-coded: Green for high, Red for low")
    print()
    print("=" * 70)
    print("Navigation:")
    print("  • Use arrow keys (↑↓) to select different dive spots")
    print("  • Tide panel updates automatically when you change selection")
    print("  • Press 'q' to quit")
    print()
    print("=" * 70)
    print()
    print("Press ENTER to launch the dashboard...")
    input()

    main()
