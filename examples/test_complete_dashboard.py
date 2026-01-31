#!/usr/bin/env python3
"""Demo of the complete Nudibranch dashboard.

This is the full application with all features enabled:
- Live conditions table for all dive spots
- Detailed tide panel with ASCII chart
- Auto-refresh every 5 minutes
- Help screen with keybindings
- Status bar with last update time

Run with: python examples/test_complete_dashboard.py
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - COMPLETE DASHBOARD")
    print("=" * 70)
    print()
    print("🌊 PHUKET FREEDIVING CONDITIONS MONITOR")
    print()
    print("FEATURES:")
    print("  ✓ Live marine conditions (waves, wind, swell)")
    print("  ✓ Harmonic tide predictions (high/low times)")
    print("  ✓ Safety assessment (SAFE/CAUTION/UNSAFE)")
    print("  ✓ Visibility estimation (GOOD/MIXED/POOR)")
    print("  ✓ Auto-refresh every 5 minutes")
    print("  ✓ Detailed tide panel with ASCII chart")
    print("  ✓ Last update tracking")
    print()
    print("DIVE SPOTS:")
    print("  • Racha Yai")
    print("  • Shark Point")
    print("  • King Cruiser Wreck")
    print("  • Koh Doc Mai")
    print("  • Anemone Reef")
    print()
    print("NAVIGATION:")
    print("  ↑/↓  - Navigate between dive spots")
    print("  r    - Manual refresh")
    print("  ?    - Show help screen")
    print("  q    - Quit")
    print()
    print("DATA SOURCES:")
    print("  • Open-Meteo Marine API (FREE)")
    print("  • Harmonic tide predictions (offline)")
    print("  • Safety & visibility calculated locally")
    print()
    print("=" * 70)
    print()
    print("Press ENTER to launch the complete dashboard...")
    input()

    main()
