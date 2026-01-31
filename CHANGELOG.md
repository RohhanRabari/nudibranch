# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-02-01

### Added - Initial Alpha Release

#### Core Features
- **Terminal UI Dashboard** - Beautiful Textual-based interface with ocean theme
- **Multi-spot Monitoring** - Track conditions at multiple dive sites simultaneously
- **Real-time Marine Data** - Wave height, wind speed, swell data via Open-Meteo API
- **Tide Predictions** - Dual-mode system with Stormglass API + harmonic fallback
- **Safety Assessment** - Automatic SAFE/CAUTION/UNSAFE status with factor breakdown
- **Visibility Estimation** - GOOD/MIXED/POOR visibility based on weather conditions
- **Auto-refresh** - Automatic data updates every 5 minutes

#### Tide System
- Stormglass.io API integration for global accurate predictions
- Harmonic analysis fallback (8 tidal constituents)
- Regional scaling for tropical/temperate/polar regions
- UTC-aware timezone handling
- Professional ASCII tide charts with 24-hour forecast
- Next high/low tide times with countdowns
- AM/PM time format throughout application

#### UI Features
- 70/30 split layout (conditions table / tide panel)
- Live clock in header with AM/PM format
- Color-coded status indicators
- Arrow key navigation
- Dynamic spot management (add/remove via 'a'/'d' keys)
- Help screen with keybindings ('?' key)
- Responsive terminal interface

#### Performance
- Parallel data fetching for multiple spots
- Multi-tier caching (Redis + disk fallback)
- Configurable thresholds via YAML

#### Configuration
- YAML-based spot configuration
- YAML-based safety thresholds
- Environment variable support via .env
- Example configuration files included

### Technical Details
- **Language**: Python 3.11+
- **Framework**: Textual TUI
- **APIs**: Open-Meteo (free), Stormglass.io (free tier), Copernicus Marine (optional)
- **Test Coverage**: 67 tests passing
- **Lines of Code**: ~2,500 (code + tests + examples)

### Documentation
- Comprehensive README with setup instructions
- API integration guides
- Tide fallback system documentation
- Configuration examples
- Contributing guidelines

### Dependencies
- httpx>=0.25.0 - HTTP client
- textual>=0.47.0 - Terminal UI framework
- pydantic>=2.5.0 - Data validation
- pyyaml>=6.0.1 - YAML parsing
- python-dotenv>=1.0.0 - Environment variables
- numpy>=1.24.0 - Tide calculations
- rich>=13.7.0 - Terminal formatting
- And more (see requirements.txt)

### Known Limitations (Alpha)
- No historical data tracking yet
- No export functionality
- No alerts/notifications
- Limited to configured dive spots
- Copernicus turbidity data is optional

### Breaking Changes
- N/A (initial release)

### Security
- API keys stored in .env (gitignored)
- No sensitive data logged
- HTTPS only for API calls

---

**Note**: This is an alpha release intended for development testing. Please report issues on GitHub.
