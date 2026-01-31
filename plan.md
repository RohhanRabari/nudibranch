# Project Segmentation: Nudibranch

**Project Codename:** Nudibranch  
**Purpose:** Phuket Freediving Conditions Dashboard (Terminal UI)  
**Stack:** Open-Meteo + WorldTides/pyTMD + Copernicus Marine + Textual TUI  
**Scope:** Terminal dashboard for real-time sea conditions monitoring

---

## Phase 1: Core Data Layer (Foundation)

### Task 1.1: Project structure + configuration
**Goal:** Set up the project skeleton with config management

```
nudibranch/
├── pyproject.toml          # Dependencies
├── .env.example            # API keys template
├── config/
│   ├── spots.yaml          # Your dive spot lat/longs
│   └── thresholds.yaml     # Safety thresholds
├── src/
│   └── nudibranch/
│       ├── __init__.py
│       └── models.py       # Data classes
└── tests/
```

**Success criteria:**
- Can run `pip install -e .`
- Config loads dive spots from YAML
- DiveSpot dataclass with name, lat, lng, region

**Claude Code prompt:**
```
Create a Python project structure for a marine conditions dashboard. 
Include:
1. pyproject.toml with dependencies: httpx, aiocache, pydantic, pyyaml
2. Configuration loader that reads dive spots from config/spots.yaml
3. Pydantic models for DiveSpot (name, lat, lng, region, depth_range)
4. Example spots.yaml with 3 Phuket locations
5. Basic tests that config loads correctly

Follow modern Python practices (3.11+, type hints, dataclasses).
```

---

### Task 1.2: Open-Meteo API client
**Goal:** Fetch marine + weather data for a single location

**Success criteria:**
- Async function `fetch_marine_conditions(lat, lng) -> dict`
- Returns: waves, swell (primary/secondary), wind, weather
- Handles HTTP errors with retry logic (tenacity)
- Unit test with mocked response

**Claude Code prompt:**
```
Build an async API client for Open-Meteo Marine and Weather APIs.

Requirements:
1. File: src/nudibranch/clients/open_meteo.py
2. Class: OpenMeteoClient with async methods:
   - fetch_marine(lat, lng) -> dict (waves, swell, SST)
   - fetch_weather(lat, lng) -> dict (wind, rain, temp)
3. Use httpx.AsyncClient with 30s timeout
4. Add retry logic: exponential backoff, max 3 attempts
5. Parse response and return structured dict with:
   - wave_height_m, wave_period_s, wave_direction_deg
   - swell_height_m, swell_period_s, swell_direction_deg
   - wind_speed_kt, wind_direction_deg, wind_gust_kt
   - precipitation_mm, cloud_cover_pct, temperature_c
6. Include docstrings with example usage
7. Write tests with pytest-httpx for mocked responses

API docs: https://open-meteo.com/en/docs/marine-weather-api
Use hourly data, get "current" + next 24h forecast
```

---

### Task 1.3: WorldTides API client
**Goal:** Fetch tide predictions (start with WorldTides, pyTMD later)

**Success criteria:**
- `fetch_tides(lat, lng, days=7) -> dict`
- Returns high/low times + heights for next 7 days
- Parses extremes into structured format
- Handles API credit exhaustion gracefully

**Claude Code prompt:**
```
Build WorldTides API client for tide predictions.

Requirements:
1. File: src/nudibranch/clients/worldtides.py
2. Class: WorldTidesClient(api_key: str)
3. Method: async fetch_tides(lat, lng, days=7) -> dict
4. Returns structured data:
   {
     'extremes': [
       {'time': datetime, 'height_m': float, 'type': 'high'/'low'},
       ...
     ],
     'hourly_heights': [(datetime, height_m), ...]
   }
5. Handle errors: invalid coords, credit exhaustion, network issues
6. Load API key from environment: WORLDTIDES_API_KEY
7. Tests with mocked API responses

API docs: https://www.worldtides.info/apidocs
Endpoints: /v3?extremes&heights&lat={lat}&lon={lng}&key={key}
```

---

### Task 1.4: Copernicus Marine turbidity client
**Goal:** Fetch satellite turbidity for visibility proxy

**Success criteria:**
- `fetch_turbidity(lat, lng) -> float`
- Returns most recent turbidity measurement (FNU)
- Handles missing data / cloud cover
- Caches for 6 hours

**Claude Code prompt:**
```
Build Copernicus Marine Service client for turbidity data.

Requirements:
1. File: src/nudibranch/clients/copernicus.py
2. Use copernicusmarine Python package
3. Class: CopernicusClient with method:
   - async fetch_turbidity(lat, lng, days_back=3) -> Optional[float]
4. Query biogeochemical data products for turbidity (TUR variable)
5. Return most recent valid measurement within days_back window
6. Handle: no data available, cloud cover, connection issues
7. Include fallback: return None if no data found
8. Tests with sample NetCDF data

Dataset: OCEANCOLOUR_GLO_BIO_BGC_L4_NRT_009_102
Variable: turbidity (FNU units)
Note: This requires Copernicus Marine account (free registration)
Setup instructions in README
```

---

### Task 1.5: Caching layer
**Goal:** Smart caching with different TTLs per data type

**Success criteria:**
- Decorator `@cached_by_location(ttl=3600)`
- Redis-backed with diskcache fallback
- Location-based cache keys
- Manual invalidation support

**Claude Code prompt:**
```
Build intelligent caching layer for marine data with multi-tier storage.

Requirements:
1. File: src/nudibranch/cache.py
2. Class: DataCache with:
   - Primary: aiocache with Redis backend (optional)
   - Fallback: diskcache for offline operation
   - TTL configs: weather=1800s, tides=43200s, turbidity=21600s
3. Decorator: @cached_by_location(ttl, data_type)
   - Generates keys: f"{data_type}:{lat:.3f}:{lng:.3f}"
4. Methods:
   - get(key) -> Optional[Any]
   - set(key, value, ttl)
   - invalidate(key)
   - invalidate_location(lat, lng)  # Clear all data for a spot
5. Graceful degradation: if Redis unavailable, use diskcache only
6. Tests: verify TTL expiration, fallback behavior
7. Config: cache directory path, Redis connection string

Dependencies: aiocache, diskcache
```

---

## Phase 2: Business Logic

### Task 2.1: Safety assessment engine
**Goal:** Evaluate conditions against freediving safety thresholds

**Success criteria:**
- `assess_conditions(conditions: dict) -> SafetyLevel`
- Returns SAFE/CAUTION/UNSAFE based on thresholds
- Per-metric breakdown showing which factors triggered status
- Load thresholds from config/thresholds.yaml

**Claude Code prompt:**
```
Build safety assessment system for freediving conditions.

Requirements:
1. File: src/nudibranch/safety.py
2. Enum: SafetyLevel (SAFE, CAUTION, UNSAFE)
3. Load thresholds from config/thresholds.yaml:
   wind_speed_kt: {safe: 10, caution: 15, unsafe: 20}
   wave_height_m: {safe: 0.5, caution: 1.0, unsafe: 1.5}
   swell_period_s: {safe: 10, caution: 7, unsafe: 5}  # Higher=better
4. Function: assess_conditions(conditions: dict) -> dict
   Returns: {
     'overall': SafetyLevel,
     'factors': {
       'wind': {'value': 12, 'status': SafetyLevel.SAFE},
       'waves': {'value': 0.8, 'status': SafetyLevel.CAUTION},
       ...
     },
     'limiting_factor': 'waves'  # Worst condition
   }
5. Handle metrics where higher is better (swell period) vs lower is better (wind)
6. Tests with various condition combinations
7. Thresholds should be easy to customize per user preference
```

---

### Task 2.2: Visibility estimation (3-tier)
**Goal:** Proxy-based visibility indicator using turbidity + weather

**Success criteria:**
- `estimate_visibility(turbidity, weather_history) -> VisibilityLevel`
- Returns GOOD/MIXED/POOR with supporting data
- Uses 3-5 day rolling averages for weather factors
- Transparent about uncertainty

**Claude Code prompt:**
```
Build 3-tier visibility estimation system using proxy indicators.

Requirements:
1. File: src/nudibranch/visibility.py
2. Enum: VisibilityLevel (GOOD >20m, MIXED 10-20m, POOR <10m)
3. Function: estimate_visibility(
     turbidity_fnu: Optional[float],
     recent_rainfall_mm: float,  # Last 3 days
     avg_wind_speed_kt: float,   # 5-day rolling avg
     swell_height_m: float
   ) -> dict
4. Returns: {
     'level': VisibilityLevel,
     'confidence': 'low'/'medium'/'high',
     'indicators': {
       'turbidity': {'value': 1.2, 'status': 'favorable'},
       'rainfall': {'value': 0, 'status': 'favorable'},
       'sea_state': {'value': 0.4, 'status': 'favorable'}
     },
     'range_estimate': '20-30m',
     'notes': 'Based on satellite and weather proxy - not measured'
   }
5. Handle missing turbidity data (satellite cloud cover)
6. Scoring logic:
   - Low turbidity (<2 FNU) + No rain + Calm seas = GOOD
   - High turbidity (>5 FNU) + Heavy rain (>50mm) + Rough seas = POOR
   - Everything else = MIXED
7. Tests with various combinations
8. Document limitations prominently in docstrings
```

---

### Task 2.3: Data aggregator
**Goal:** Combine all data sources for a single dive spot

**Success criteria:**
- `fetch_spot_conditions(spot: DiveSpot) -> FullConditions`
- Calls all clients, handles failures gracefully
- Returns structured, display-ready data
- Logs which data sources succeeded/failed

**Claude Code prompt:**
```
Build data aggregator that combines all API sources for a dive spot.

Requirements:
1. File: src/nudibranch/aggregator.py
2. Class: ConditionsAggregator(
     open_meteo: OpenMeteoClient,
     worldtides: WorldTidesClient,
     copernicus: CopernicusClient,
     cache: DataCache
   )
3. Method: async fetch_spot_conditions(spot: DiveSpot) -> dict
   Returns comprehensive data structure with:
   - weather: {...}
   - marine: {waves, swell, wind}
   - tides: {next_high, next_low, current_height, is_rising}
   - visibility: {level, indicators, confidence}
   - safety: {overall, factors, limiting_factor}
   - metadata: {fetched_at, cache_status: {'marine': 'hit', 'tides': 'miss'}}
4. Error handling: if one source fails, continue with others
   - Mark failed sources in metadata
   - Log warnings but don't crash
5. Use caching layer for each data type
6. Calculate derived fields:
   - is_tide_rising: bool
   - time_to_next_high: timedelta
   - wind_speed_beaufort: int
7. Tests with partial failures (one API down)
```

---

## Phase 3: Terminal Dashboard (Complete Application)

### Task 3.1: Basic Textual app skeleton
**Goal:** Empty app with layout structure

**Claude Code prompt:**
```
Build Textual TUI app skeleton for marine conditions dashboard.

Requirements:
1. File: src/nudibranch/tui/app.py
2. Class: NudibranchApp(App)
3. Layout structure:
   - Header: Title + clock
   - Main: 70% conditions table | 30% tide panel
   - Footer: Keybindings (r=refresh, q=quit, s=select spot)
4. CSS styling:
   - Color scheme: ocean blues/teals
   - Safe=green, Caution=yellow, Unsafe=red classes
5. Load dive spots from config on startup
6. Empty widgets for now (populate in next tasks)
7. Basic keyboard navigation works
8. Can run with: python -m nudibranch.tui
```

---

### Task 3.2: Conditions table widget
**Goal:** Display multi-spot conditions in DataTable

**Claude Code prompt:**
```
Build conditions table for Textual dashboard showing multiple dive spots.

Requirements:
1. File: src/nudibranch/tui/widgets/conditions_table.py
2. Use Textual's DataTable widget
3. Columns: Spot | Waves | Wind | Swell | Tide | Visibility | Status
4. Rows: One per dive spot from config
5. Populate using ConditionsAggregator data
6. Color-coded status column (green/yellow/red)
7. Format values nicely:
   - Waves: "0.8m / 6s"
   - Wind: "12kt NE"
   - Tide: "Rising → High 14:30" or "Falling → Low 08:15"
   - Visibility: "🟢 Good" / "🟡 Mixed" / "🔴 Poor"
8. Show loading spinner while fetching
9. Handle fetch errors gracefully (show "Error" in row)
10. Update method: refresh_data(spots: List[DiveSpot])
```

---

### Task 3.3: Tide panel widget
**Goal:** Detailed tide info for selected spot

**Claude Code prompt:**
```
Build tide detail panel for Textual dashboard.

Requirements:
1. File: src/nudibranch/tui/widgets/tide_panel.py
2. Display for selected dive spot:
   - Current tide height: "1.2m (Rising)"
   - Next high: "14:30 (2.4m) - in 3h 15m"
   - Next low: "20:45 (0.3m) - in 9h 30m"
   - ASCII chart of tide curve for next 24h
3. Use rich's Tree or Panel for formatting
4. Highlight optimal dive window (rising tide period)
5. Update method: display_tides(spot_name, tide_data)
6. Handle missing tide data (show placeholder)
7. Visual indicator: ↑ Rising / ↓ Falling / ⟷ Slack
```

---

### Task 3.4: Auto-refresh + data management
**Goal:** Background workers for periodic updates

**Claude Code prompt:**
```
Add auto-refresh and background data fetching to Textual app.

Requirements:
1. Modify app.py to include:
2. Use Textual's @work decorator for async data fetching
3. set_interval(300, refresh_all_spots)  # Every 5 minutes
4. Worker pool: fetch spots in parallel (aiometer, max 5 concurrent)
5. Show "Last updated: 2m ago" in footer
6. Manual refresh on 'r' key press
7. Show spinner/status during refresh
8. Handle network errors: keep old data, show warning
9. Graceful shutdown: cancel workers on quit
10. Log refresh attempts and failures
```

---

### Task 3.5: Polish + configuration UI
**Goal:** Spot selection, error states, help screen

**Claude Code prompt:**
```
Add final polish to Textual dashboard.

Requirements:
1. Spot selection: Press 's' to open modal with spot list
   - Select spot to see details in tide panel
   - Highlight selected row in table
2. Help screen: Press '?' for keybindings reference
3. Error states:
   - API down: Show warning banner
   - No internet: Switch to cached data mode
   - Invalid config: Show helpful error on startup
4. Configuration panel: Press 'c' to edit thresholds
   - Simple form to adjust safety thresholds
   - Save back to config/thresholds.yaml
5. Status indicators in footer:
   - 🟢 All systems operational
   - 🟡 Degraded (cached data only)
   - 🔴 No data available
6. Add --debug flag for verbose logging
7. Package as standalone script with entry point
```

---

## Implementation Workflow

### Sequential approach:
```bash
# Phase 1: Core data layer foundation
Task 1.1 → 1.2 → 1.3 → 1.4 → 1.5

# Phase 2: Business logic
Task 2.1 → 2.2 → 2.3

# Phase 3: Terminal dashboard (complete application)
Task 3.1 → 3.2 → 3.3 → 3.4 → 3.5
```

### Key advantages:
- ✅ Each task is **self-contained** (2-4 hours max)
- ✅ Clear **acceptance criteria** (you know when it's done)
- ✅ **Testable** at each step
- ✅ **Progressive** (builds up complexity gradually)
- ✅ Can **pause/resume** between tasks
- ✅ Terminal-focused = faster to complete, lower complexity

### Testing checkpoints:
- After Task 1.5: Run integration test fetching all data for one spot
- After Task 2.3: Verify full conditions aggregation works end-to-end
- After Task 3.5: Terminal dashboard fully functional and production-ready

---

## Optional Future Enhancements

### Phase 4: Advanced Terminal Features (post-MVP)
- **pyTMD integration** (Task 1.3b): Replace WorldTides with local harmonic calculations
- **Historical analysis**: Track condition patterns over months
- **Notification system**: Terminal notifications or SMS/email alerts when conditions become optimal
- **Dive log integration**: Track actual visibility observations and correlate with predictions
- **Multi-region support**: Extend beyond Phuket to Similan, Phi Phi, Krabi
- **Export functionality**: CSV/JSON export of current conditions
- **Configuration TUI**: Enhanced in-terminal configuration editor

### Phase 5: Web Dashboard (v2 - Future)
If you later decide to build a web interface, the data layer (Phase 1) and business logic (Phase 2) are fully reusable:
- NiceGUI or Streamlit web dashboard
- Interactive Leaflet map with dive spot markers
- Plotly tide visualizations
- Mobile-responsive PWA
- Dive buddy network features
- Shareable condition snapshots

### Phase 6: Advanced Integrations (Future)
- **Marine monitoring buoy integration**: Real sensor data from your ESP32 buoys
- **ML visibility prediction**: Train model on your dive logs + conditions
- **Mobile app**: React Native wrapper (if web version exists)
- **API service**: Expose conditions data for other applications

---

## Estimated Timeline

| Phase | Tasks | Est. Time | Deliverable |
|-------|-------|-----------|-------------|
| Phase 1 | 5 tasks | 2-3 days | Data layer working |
| Phase 2 | 3 tasks | 1-2 days | Business logic complete |
| Phase 3 | 5 tasks | 2-3 days | **Terminal dashboard complete** |
| **Total** | **13 tasks** | **~1 week** | Production-ready terminal application |

*Timeline assumes working 2-4 hours per day, with testing and iteration*

**MVP Goal:** Fully functional terminal dashboard that monitors multiple Phuket dive spots with real-time conditions, tide predictions, and safety assessments.
