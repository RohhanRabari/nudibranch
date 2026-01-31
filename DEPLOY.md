# Deployment Guide - v0.0.1 Alpha Release

## Current Status

✅ **Initial commit created** - 60 files committed
✅ **Version set to 0.0.1** - Updated in pyproject.toml and __init__.py
✅ **Release tagged** - v0.0.1 tag created
✅ **Requirements files created** - requirements.txt and requirements-dev.txt
✅ **License added** - MIT License
✅ **Changelog created** - Comprehensive release notes
✅ **README updated** - Complete setup instructions with bash commands

## Push to GitHub

### 1. Create GitHub Repository

Go to GitHub and create a new repository named `nudibranch`

### 2. Add Remote and Push

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/nudibranch.git

# Or if using SSH:
git remote add origin git@github.com:YOUR_USERNAME/nudibranch.git

# Push the main branch
git push -u origin main

# Push the release tag
git push origin v0.0.1
```

### 3. Create GitHub Release (Optional)

Go to your GitHub repository → Releases → Create a new release:
- Tag: `v0.0.1`
- Title: `Alpha Release v0.0.1`
- Description: Copy from CHANGELOG.md
- Mark as "pre-release" since it's alpha

## Testing on Your Laptop

### 1. Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/nudibranch.git
cd nudibranch
```

### 2. Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# OR install in editable mode (recommended for testing)
pip install -e .
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your editor
nano .env
```

Add your Stormglass API key (get free key at https://stormglass.io/):
```bash
STORMGLASS_API_KEY=your_api_key_here
```

### 5. Run the Dashboard

```bash
# Make sure venv is activated
source .venv/bin/activate

# Run via Python module
python -m nudibranch.tui.app

# OR if installed with pip install -e .
nudibranch
```

### 6. Test Features

Once running:
- Press `a` to add a new dive spot
- Press `↑/↓` to navigate between spots
- Press `r` to manually refresh data
- Press `?` to see help screen
- Press `q` to quit

### 7. Run Tests (Optional)

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=nudibranch

# Run specific test file
pytest tests/test_tides.py -v
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Deactivate current venv
deactivate

# Remove old venv
rm -rf .venv

# Create fresh venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Missing Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### API Issues

If you see "API failed, using harmonic fallback":
- This is normal if you haven't configured STORMGLASS_API_KEY
- The app will work with calculated tides (less accurate but functional)
- Get a free API key at https://stormglass.io/ for better accuracy

### Slow Loading

First load may be slow while fetching data:
- All spots fetch in parallel (should take 5-10 seconds)
- Data is cached after first fetch
- Press `r` to manually refresh if needed

## What's Included

### Source Code
- `src/nudibranch/` - Main application code
  - `clients/` - API clients (Open-Meteo, Tides, Copernicus)
  - `tui/` - Terminal UI components
    - `widgets/` - Custom widgets (table, tide panel, etc.)
  - `aggregator.py` - Data aggregation
  - `safety.py` - Safety assessment
  - `visibility.py` - Visibility estimation
  - `cache.py` - Multi-tier caching
  - `config.py` - Configuration management
  - `models.py` - Data models

### Configuration
- `config/spots.yaml` - Dive spot locations (editable)
- `config/thresholds.yaml` - Safety thresholds (editable)
- `.env.example` - Environment variables template

### Tests
- `tests/` - 67 tests covering all modules
- Run with `pytest`

### Documentation
- `README.md` - Main documentation
- `CHANGELOG.md` - Release notes
- `TIDE_FALLBACK_SYSTEM.md` - Tide system details
- `FREE_APIS.md` - API information
- `SPOT_MANAGEMENT.md` - Spot management guide

### Examples
- `examples/` - Demo scripts for testing individual components

## Version Info

- **Version**: 0.0.1 (Alpha)
- **Python**: 3.11+
- **Commit**: 669acbb
- **Tag**: v0.0.1
- **Date**: 2026-02-01

## Next Steps

After testing on your laptop:
1. Report any bugs via GitHub Issues
2. Test with different dive locations worldwide
3. Verify tide predictions match real data
4. Test performance with multiple spots
5. Provide feedback for v0.0.2

---

**Happy Diving! 🌊**
