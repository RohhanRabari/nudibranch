# Nudibranch 🌊

**Production-ready terminal dashboard for monitoring dive conditions worldwide.**

Beautiful, real-time dive conditions monitoring right in your terminal using 100% FREE APIs. Track conditions anywhere in the world - from tropical reefs to temperate dive sites.

## Features

✅ **Live Marine Conditions**
- Wave height, period, and direction
- Wind speed, direction, and gusts
- Swell height, period, and direction
- Sea temperature and cloud cover

✅ **Tide Predictions**
- Harmonic tide calculations (offline, no API needed)
- Current tide height and direction (rising/falling)
- Next high and low tide times with countdowns
- Professional ASCII tide chart with:
  - Y-axis labels (tide height in meters)
  - X-axis labels (time: 0h, 6h, 12h, 18h, 24h)
  - Grid dots for easy reading
  - Smooth interpolated curve (cosine interpolation)
  - Marked high (▲) and low (▼) tide peaks
- Upcoming tide extremes list

✅ **Weather Information**
- Current temperature (°C and °F)
- Cloud cover with visual icons
- Precipitation levels
- Wind speed, direction, and gusts
- All displayed in the tide panel

✅ **Safety Assessment**
- Automatic safety evaluation (SAFE/CAUTION/UNSAFE)
- Color-coded status indicators
- Per-factor breakdown (wind, waves, swell)
- Identifies limiting safety factors
- Customizable thresholds

✅ **Visibility Estimation**
- 3-tier visibility levels (GOOD/MIXED/POOR)
- Estimates based on weather proxies
- Optional satellite turbidity integration
- Confidence level reporting

✅ **Multi-Spot Monitoring**
- Monitor multiple dive sites simultaneously
- Add/remove spots dynamically (press 'a' or 'd')
- Side-by-side comparison
- Arrow key navigation
- Auto-refresh every 5 minutes
- Changes saved automatically

✅ **Terminal UI**
- Ocean-themed color scheme
- Responsive layout (70/30 split)
- Live status updates
- Help screen with keybindings
- No external dependencies except Python

## Installation

### Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/RohhanRabari/nudibranch.git
cd nudibranch
```

### Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# OR install in development mode (recommended)
pip install -e .

# For development with testing tools
pip install -r requirements-dev.txt
```

### Configure API Keys (Optional but Recommended)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add your Stormglass API key:
```bash
STORMGLASS_API_KEY=your_api_key_here
```

Get a free API key at https://stormglass.io/ (50 requests/day free tier)

## Quick Start

### Run the Dashboard

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Run the dashboard
python -m nudibranch.tui.app

# OR if you installed with pip install -e .
nudibranch
```

### First Time Setup

1. **Add your first dive spot**: Press `a` to add a new location
2. **Navigate**: Use arrow keys ↑/↓ to move between spots
3. **View details**: Select a spot to see tide chart and weather
4. **Refresh**: Press `r` to manually refresh data

That's it! The app works with harmonic tide fallback even without API keys.

## Configuration

### Required: Stormglass.io API Key

For accurate global tide predictions:

1. Register at https://stormglass.io/ (free tier: 50 requests/day)
2. Get your API key from the dashboard
3. Copy `.env.example` to `.env`
4. Add your API key:
```bash
STORMGLASS_API_KEY=your_api_key_here
```

### Optional: Satellite Turbidity Data

For enhanced visibility predictions, set up Copernicus Marine (100% FREE):

1. Register at https://marine.copernicus.eu/
2. Add your credentials to `.env`:
```bash
COPERNICUSMARINE_SERVICE_USERNAME=your_email@example.com
COPERNICUSMARINE_SERVICE_PASSWORD=your_password
```

### Customization

- **Dive spots:**
  - Add spots in-app by pressing **a** (saved to `config/spots.yaml`)
  - Remove spots in-app by pressing **d** on selected spot
  - Or manually edit `config/spots.yaml`
- **Safety thresholds:** Adjust `config/thresholds.yaml` to match your comfort level
- Both files support YAML syntax with comments

### Managing Dive Spots

**Add a new spot (press 'a'):**
1. Enter the spot name (e.g., "Similan Islands")
2. Enter coordinates (latitude and longitude)
3. Optionally add region, depth range, and description
4. Changes are saved automatically to `config/spots.yaml`
5. Data is fetched immediately for the new spot

**Delete a spot (press 'd'):**
1. Navigate to the spot you want to remove using ↑/↓
2. Press 'd' to delete
3. Confirm the deletion
4. Changes are saved automatically to `config/spots.yaml`

## Usage

```bash
# Launch the dashboard
nudibranch

# Or via Python module
python -m nudibranch.tui.app

# Run demo scripts
python examples/test_complete_dashboard.py
```

### Keybindings

- **↑/↓** - Navigate between dive spots
- **a** - Add new dive spot
- **d** - Delete selected dive spot
- **r** - Manually refresh all data
- **?** - Show help screen
- **q** - Quit application

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ 🌊 NUDIBRANCH - Dive Conditions Dashboard   2026-01-31 12:00 PM   │
├──────────────────────────────────────┬─────────────────────────────┤
│ CONDITIONS TABLE (70%)               │ TIDE PANEL (30%)            │
│                                      │                             │
│ Spot            Waves    Wind  Swell │ 🌙 Your Dive Site           │
│ ────────────────────────────────     │ ════════════════            │
│ Site Alpha      0.5m@4s  12kt  1.0m  │ CURRENT TIDE                │
│ Site Beta       0.6m@4s  11kt  0.9m  │   1.54m ↓ FALLING           │
│ Site Gamma      0.5m@4s  10kt  1.1m  │                             │
│ Site Delta      0.7m@5s  13kt  0.8m  │ NEXT EVENTS                 │
│ Site Epsilon    0.6m@4s  12kt  1.0m  │   ↑ High: 03:30 PM (2.13m)  │
│                                      │          in 3h 15m          │
│ Status: ✓ SAFE / ⚠ CAUTION / ✗ UNSAFE│   ↓ Low:  09:45 AM (0.32m)  │
│ Visibility: 🟢 Good / 🟡 Mixed / 🔴 Poor│          in 9h 30m          │
│                                      │                             │
│                                      │ TIDE CURVE (24H)            │
│                                      │ 2.5m|      ·▲·   ·+        │
│                                      │ 2.0m|   ·++· ·+·  ·        │
│                                      │ 1.5m| ·+·      ·+·         │
│                                      │ 1.0m|+          ▼          │
│                                      │     +-------------------+  │
│                                      │     0h  6h  12h 18h 24h    │
│                                      │                             │
│                                      │ WEATHER                     │
│                                      │   🌡️ Temp: 28.5°C (83°F)    │
│                                      │   ☀️ Cloud: 15% (Clear)     │
│                                      │   💨 Wind: 12kt NE          │
└──────────────────────────────────────┴─────────────────────────────┘
│ 🟢 Last updated: 2m ago - Auto-refresh in 178s                    │
│ r Refresh  ? Help  q Quit                                         │
└────────────────────────────────────────────────────────────────────┘
```

## Development Status

**✅ PRODUCTION READY - All phases complete!**

- ✅ **Phase 1:** Data Layer (5 tasks)
  - API clients (Open-Meteo, Tides, Copernicus)
  - Multi-tier caching (Redis + disk fallback)
  - Configuration management

- ✅ **Phase 2:** Business Logic (3 tasks)
  - Safety assessment engine
  - Visibility estimation
  - Data aggregator

- ✅ **Phase 3:** Terminal Dashboard (5 tasks)
  - Textual TUI framework
  - Live conditions table
  - Detailed tide panel
  - Auto-refresh system
  - Help screen and polish

**Test Coverage:** 67 tests passing
**Total Code:** ~2,500 lines (code + tests + examples)

See `PHASE3_PROGRESS.md` for detailed feature documentation.

## Data Sources

**100% FREE APIs - No subscriptions, no credit cards required!**

### Open-Meteo Marine API (Primary)
- ✅ **FREE** forever - No API key needed
- Wave height, period, direction
- Wind speed, direction, gusts
- Sea temperature, cloud cover
- Swell data (height, period, direction)
- https://open-meteo.com/

### Stormglass.io Tide Predictions
- ✅ **FREE** tier - 50 requests/day
- Global coverage with 5,000+ tide stations
- Accurate tide predictions for any location worldwide
- Automatic station selection based on coordinates
- Register at https://stormglass.io/ for free API key

### Copernicus Marine Service (Optional)
- ✅ **FREE** - EU-funded public service
- Satellite turbidity data (FNU)
- Guaranteed free through 2028+
- Optional - app works without it
- https://marine.copernicus.eu/

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=nudibranch

# Run specific test suite
pytest tests/test_tui_app.py -v

# Type checking
mypy src/nudibranch
```

## Project Structure

```
nudibranch/
├── config/
│   ├── spots.yaml          # Dive spot locations
│   └── thresholds.yaml     # Safety thresholds
├── src/nudibranch/
│   ├── clients/            # API clients
│   │   ├── open_meteo.py   # Marine weather
│   │   ├── tides.py        # Tide predictions
│   │   └── copernicus.py   # Turbidity (optional)
│   ├── tui/                # Terminal UI
│   │   ├── app.py          # Main application
│   │   └── widgets/        # Custom widgets
│   ├── aggregator.py       # Data aggregator
│   ├── safety.py           # Safety assessment
│   ├── visibility.py       # Visibility estimation
│   ├── cache.py            # Caching layer
│   ├── config.py           # Configuration loader
│   └── models.py           # Data models
├── tests/                  # Test suite (67 tests)
└── examples/               # Demo scripts
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Roadmap (Future Enhancements)

- [ ] Historical data tracking and trend analysis
- [ ] Export conditions to CSV/JSON
- [ ] SMS/email alerts for optimal conditions
- [ ] Dive log integration
- [ ] Mobile app (React Native)
- [ ] Support for more data sources

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Open-Meteo** for excellent free marine API
- **Copernicus Marine** for satellite data
- **Textual** for the TUI framework
- **Pydantic** for data validation
