# Free API Usage - No Costs

This project is designed to use **completely free** data sources with no API costs.

## Current Data Sources

### ✅ Open-Meteo API (FREE)
- **Service:** Marine weather & wave data
- **Cost:** FREE - No API key required
- **Usage:** Unlimited for non-commercial use
- **Data:** Waves, swell, wind, weather conditions
- **Docs:** https://open-meteo.com/en/docs/marine-weather-api

### ✅ Tide Predictions (FREE - Offline)
- **Method:** Harmonic analysis using tidal constituents
- **Cost:** FREE - No API calls, runs offline
- **Library:** Custom implementation using numpy
- **Data:** High/low tides, hourly heights
- **Note:** Simplified model - good for general use, validate against local tide tables for critical decisions

## Future Data Sources (Planned)

### Copernicus Marine (FREE with registration)
- **Service:** Satellite turbidity data for visibility estimation
- **Cost:** FREE with account registration
- **Usage:** Free for research and non-commercial use
- **Data:** Ocean color, turbidity (FNU), chlorophyll
- **Registration:** https://marine.copernicus.eu/

## Architecture Decision: Free-First

We intentionally chose free alternatives over paid APIs:

1. **WorldTides API** → Replaced with harmonic tide predictions
   - WorldTides costs ~$0.60/month for our usage
   - Harmonic predictions are free and offline
   - Trade-off: Slightly less accurate but sufficient for dive planning

2. **Open-Meteo** → No commercial alternative needed
   - Already free and excellent quality
   - No usage limits for non-commercial projects

3. **Copernicus Marine** → Free with registration
   - Official EU program for ocean monitoring
   - Free for research and education
   - May add later for visibility estimates

## Cost Comparison

| Service | Alternative | Monthly Cost | Our Choice |
|---------|-------------|--------------|------------|
| Tides | WorldTides API | $0.60+ | FREE (Harmonic) |
| Marine Weather | StormGlass | $50+ | FREE (Open-Meteo) |
| Turbidity | Commercial satellite | $100+ | FREE (Copernicus) |
| **TOTAL** | | **$150+** | **$0.00** |

## Notes for Production Use

While our free solutions are excellent for:
- Personal dive planning
- Learning and development
- General condition monitoring

For **mission-critical** applications, consider:
- Validating tide predictions against official local tables
- Cross-referencing weather data with multiple sources
- Adding real-time sensor data (buoys, weather stations)

## Contributing

If you find other high-quality free data sources for marine conditions, please contribute!
