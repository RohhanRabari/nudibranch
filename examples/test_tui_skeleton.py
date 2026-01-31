#!/usr/bin/env python3
"""Demo of the Textual TUI skeleton.

This shows the basic app structure with placeholder widgets.
Run with: python examples/test_tui_skeleton.py

Press 'q' to quit.
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("Starting Nudibranch TUI skeleton demo...")
    print()
    print("Layout features:")
    print("  - Header with live clock")
    print("  - 70/30 split: Conditions Table | Tide Panel")
    print("  - Footer with keybindings")
    print("  - Ocean-themed color scheme")
    print()
    print("Key bindings:")
    print("  r - Refresh data (placeholder)")
    print("  s - Select spot (placeholder)")
    print("  q - Quit")
    print("  ? - Help (placeholder)")
    print()
    print("Press ENTER to launch the TUI...")
    input()

    main()
