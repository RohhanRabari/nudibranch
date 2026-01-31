#!/usr/bin/env python3
"""Demo of the spot management features.

The dashboard now supports adding and removing dive spots dynamically:
- Press 'a' to add a new dive spot
- Press 'd' to delete the currently selected spot

All changes are saved to config/spots.yaml automatically.

Run with: python examples/test_spot_management.py
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - SPOT MANAGEMENT DEMO")
    print("=" * 70)
    print()
    print("🌊 NEW FEATURES: Add & Remove Dive Spots!")
    print()
    print("SPOT MANAGEMENT:")
    print("  a  - Add a new dive spot")
    print("       • Enter spot name, coordinates, region, depth, description")
    print("       • Changes saved to config/spots.yaml")
    print("       • Data fetched automatically")
    print()
    print("  d  - Delete the currently selected spot")
    print("       • Navigate to a spot with ↑/↓")
    print("       • Press 'd' to delete")
    print("       • Confirmation dialog prevents accidents")
    print("       • Changes saved to config/spots.yaml")
    print()
    print("EXAMPLE WORKFLOW:")
    print("  1. Launch dashboard")
    print("  2. Press 'a' to add a new spot")
    print("  3. Enter details:")
    print("     - Name: Similan Islands")
    print("     - Latitude: 8.6542")
    print("     - Longitude: 97.6417")
    print("     - Region: Similan National Park")
    print("     - Depth: 5-30m")
    print("     - Description: Crystal clear water, abundant marine life")
    print("  4. Watch as data loads automatically")
    print("  5. Navigate to any spot and press 'd' to remove it")
    print()
    print("=" * 70)
    print("OTHER KEYBINDINGS:")
    print("  ↑/↓  - Navigate between dive spots")
    print("  r    - Refresh all data")
    print("  ?    - Show help")
    print("  q    - Quit")
    print()
    print("=" * 70)
    print()
    print("Press ENTER to launch the dashboard...")
    input()

    main()
