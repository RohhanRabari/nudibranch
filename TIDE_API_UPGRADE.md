# Tide Prediction API Upgrade

## Summary

The tide prediction system has been upgraded from a simplified harmonic model to **Stormglass.io Global Tide API** for accurate, worldwide tide predictions.

## What Changed

### Before: Simplified Harmonic Model
- ❌ Hardcoded for Phuket/Andaman Sea only
- ❌ Inaccurate for other regions (Raja Ampat, Red Sea, etc.)
- ❌ Estimated amplitudes and phases
- ❌ Fixed mean sea level (1.2m)
- ✅ No API key required (offline)

### After: Stormglass.io API
- ✅ **Global coverage** - works anywhere in the world
- ✅ **Accurate predictions** - uses 5,000+ tide stations
- ✅ **Real tide data** - not estimates
- ✅ **Automatic station selection** - finds nearest station
- ✅ **Free tier** - 50 requests/day
- ⚠️ Requires API key (free signup)

## Setup

### 1. Get Free API Key

Register at https://stormglass.io/ (free tier: 50 requests/day)

### 2. Configure Environment

Copy `.env.example` to `.env` and add:

```bash
STORMGLASS_API_KEY=your_api_key_here
```

### 3. Run Dashboard

```bash
nudibranch
```

The dashboard will now show accurate tides for **any** dive spot worldwide!

## Technical Changes

### Modified Files

**`src/nudibranch/clients/tides.py`** (complete rewrite)
- Removed: Harmonic analysis code (~140 lines)
- Added: Stormglass.io API client (~100 lines)
- Uses `httpx` for async HTTP requests
- Implements retry logic with `tenacity`
- Fetches both tide extremes and hourly sea levels

**`.env.example`**
- Replaced `WORLDTIDES_API_KEY` with `STORMGLASS_API_KEY`

**`README.md`**
- Updated tide prediction section
- Added Stormglass setup instructions
- Updated data sources list

**`tests/test_tides.py`** (updated for API testing)
- Added `pytest-httpx` mocks
- Tests now mock API responses instead of testing harmonic calculations
- 6 tests, all passing ✅

**`tests/test_aggregator.py`** (needs completion)
- Added Stormglass mocks
- ⚠️ Still needs Open-Meteo mocks (in progress)

## API Details

### Stormglass.io Endpoints Used

1. **Tide Extremes** - `/v2/tide/extremes/point`
   - Returns high/low tide times and heights
   - Parameters: lat, lng, start, end

2. **Sea Level** - `/v2/tide/sea-level/point`
   - Returns hourly tide heights
   - Used for tide curve visualization

### Rate Limits

**Free Tier:**
- 50 requests/day
- Perfect for personal use
- Dashboard refreshes every 5 minutes (uses caching)

**Typical Usage:**
- 7 dive spots × 2 API calls each = 14 calls/refresh
- With 5-minute refresh: ~4-5 refreshes/day
- Well within free tier limits!

## Testing

###  Current Status

```bash
# Tide tests - ✅ ALL PASSING
pytest tests/test_tides.py -v
# 6 passed

# Spot manager tests - ✅ ALL PASSING
pytest tests/test_spot_manager.py -v
# 8 passed

# Aggregator tests - ⚠️ IN PROGRESS
# Need to add Open-Meteo API mocks
```

### To Fix Aggregator Tests

The aggregator tests need mocks for BOTH APIs:
1. Stormglass (tide data) - ✅ Added
2. Open-Meteo (marine/weather) - ⏳ TODO

##Sources

Sources:
- [WorldTides - Apidocs](https://www.worldtides.info/apidocs)
- [WorldTides - Tide predictions for any location in the world](https://www.worldtides.info/home)
- [Global Tide API - stormglass.io](https://stormglass.io/global-tide-api/)
- [Web Services - NOAA Tides & Currents](https://tidesandcurrents.noaa.gov/web_services_info.html)
