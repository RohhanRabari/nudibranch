#!/usr/bin/env python3
"""Demo of the improved smooth tide curve visualization.

The tide curve now features:
- Interpolated points between tide extremes
- Smooth sinusoidal curve representation
- Visual characters showing tide direction:
  / - Rising tide
  \ - Falling tide
  ▲ - High tide peak
  ▼ - Low tide trough
  • - Curve points

Instead of just 4 discrete points, the curve now shows a realistic
tidal pattern with dozens of interpolated points creating a smooth
visual representation.

Run with: python examples/test_smooth_tide_curve.py
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - SMOOTH TIDE CURVE DEMO")
    print("=" * 70)
    print()
    print("🌊 PROFESSIONAL TIDE CHART VISUALIZATION!")
    print()
    print("The tide curve now includes professional features:")
    print()
    print("FEATURES:")
    print("  ✓ Y-axis with tide height labels (in meters)")
    print("  ✓ X-axis with time labels (0h, 6h, 12h, 18h, 24h)")
    print("  ✓ Grid dots for easy reading")
    print("  ✓ Border frame around the chart")
    print("  ✓ Smooth interpolated curve")
    print()
    print("CURVE CHARACTERS:")
    print("  +  - Curve points (rising and falling)")
    print("  ─  - Nearly flat sections")
    print("  ▲  - High tide peak")
    print("  ▼  - Low tide trough")
    print("  ·  - Grid reference dots")
    print()
    print("Example chart:")
    print(" 2.5m|      ·▲·   ·+·      |")
    print(" 2.0m|   ·++· ·+·  ·+·     |")
    print(" 1.5m| ·+·      ·+·   ·+·  |")
    print(" 1.0m|+          ▼      ·+ |")
    print("     +---------------------+")
    print("      0h  6h  12h 18h  24h")
    print()
    print("=" * 70)
    print("NAVIGATION:")
    print("  ↑/↓  - Select different dive spots to see their tide curves")
    print("  r    - Refresh data")
    print("  q    - Quit")
    print()
    print("=" * 70)
    print()
    print("Press ENTER to launch the dashboard...")
    input()

    main()
