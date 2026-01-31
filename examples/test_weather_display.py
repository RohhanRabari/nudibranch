#!/usr/bin/env python3
"""Demo of the weather information display in the tide panel.

The tide panel now shows:
- Current tide information
- Next high/low tide events
- Upcoming tides list
- WEATHER SECTION (NEW!)
  - Temperature (°C and °F)
  - Cloud cover with icons
  - Precipitation
  - Wind speed and direction

Run with: python examples/test_weather_display.py
"""

from nudibranch.tui.app import main

if __name__ == "__main__":
    print("=" * 70)
    print(" NUDIBRANCH - WEATHER DISPLAY DEMO")
    print("=" * 70)
    print()
    print("🌊 The tide panel now includes WEATHER INFORMATION!")
    print()
    print("NEW WEATHER SECTION shows:")
    print("  🌡️  Temperature - in both Celsius and Fahrenheit")
    print("  ☀️  Cloud Cover - percentage with weather icons")
    print("       ☀️ Clear (<20%)")
    print("       🌤️ Partly Cloudy (20-50%)")
    print("       ⛅ Cloudy (50-80%)")
    print("       ☁️ Overcast (>80%)")
    print("  🌧️  Precipitation - current rainfall in mm")
    print("  💨 Wind - speed in knots with direction and gusts")
    print()
    print("The weather section appears below the upcoming tides list.")
    print()
    print("=" * 70)
    print("NAVIGATION:")
    print("  ↑/↓  - Select different dive spots")
    print("  r    - Refresh all data")
    print("  ?    - Show help")
    print("  q    - Quit")
    print()
    print("=" * 70)
    print()
    print("Press ENTER to launch the dashboard...")
    input()

    main()
