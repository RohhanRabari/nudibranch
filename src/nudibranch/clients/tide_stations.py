"""Tide station registry for published tide table data.

Loads station data from config/tide_stations.yaml and provides
location-based lookup with cosine-interpolated hourly predictions.
"""

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml
from zoneinfo import ZoneInfo


class TideStationRegistry:
    """Registry of tide stations with published extremes data.

    Loads station metadata and daily high/low tables from YAML config,
    provides nearest-station lookup via haversine distance, and generates
    hourly height predictions via cosine interpolation between extremes.
    """

    def __init__(self, config_path: Path) -> None:
        self.stations: list[dict[str, Any]] = []
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
            self.stations = data.get("stations", [])

    def find_nearest_station(
        self, lat: float, lng: float, max_km: float = 50.0
    ) -> Optional[dict[str, Any]]:
        """Find the nearest station within max_km of the given coordinates.

        Args:
            lat: Query latitude
            lng: Query longitude
            max_km: Maximum search radius in kilometers

        Returns:
            Station dict if found within range, else None
        """
        best = None
        best_dist = max_km

        for station in self.stations:
            dist = self._haversine(lat, lng, station["lat"], station["lng"])
            if dist < best_dist:
                best_dist = dist
                best = station

        return best

    def get_prediction(
        self, station: dict[str, Any], start_utc: datetime, days: int
    ) -> dict[str, Any]:
        """Generate tide prediction from published extremes.

        Looks up published extremes for the requested date range,
        converts local times to UTC, and interpolates hourly heights
        via cosine curves between consecutive extremes.

        Args:
            station: Station dict from the registry
            start_utc: Start time in UTC
            days: Number of days to predict

        Returns:
            Dict matching TideClient.fetch_tides() format:
            {extremes, hourly_heights, fetched_at, source}
        """
        tz = ZoneInfo(station["timezone"])
        year = station["year"]
        extremes_data = station.get("extremes", {})

        # Collect extremes for requested date range (with 1-day padding on each side)
        local_start = start_utc.astimezone(tz)
        raw_extremes: list[dict[str, Any]] = []

        for day_offset in range(-1, days + 2):
            day = (local_start + timedelta(days=day_offset)).date()
            if day.year != year:
                continue
            key = day.strftime("%m-%d")
            day_extremes = extremes_data.get(key, [])

            for ext in day_extremes:
                hour, minute = map(int, ext["time"].split(":"))
                local_dt = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)
                utc_dt = local_dt.astimezone(timezone.utc)
                raw_extremes.append({
                    "time": utc_dt,
                    "height_m": ext["height_m"],
                    "type": ext["type"],
                })

        # Sort by time and deduplicate
        raw_extremes.sort(key=lambda e: e["time"])

        # Filter to requested window (keep some padding for interpolation)
        end_utc = start_utc + timedelta(days=days)
        window_start = start_utc - timedelta(hours=6)
        window_end = end_utc + timedelta(hours=6)
        extremes = [e for e in raw_extremes if window_start <= e["time"] <= window_end]

        # Generate hourly heights via cosine interpolation
        hourly_heights: list[tuple[datetime, float]] = []

        if len(extremes) >= 2:
            # Generate hourly time points
            t = start_utc
            while t <= end_utc:
                height = self._interpolate_height(extremes, t)
                if height is not None:
                    hourly_heights.append((t, height))
                t += timedelta(hours=1)

        # Filter extremes for output: include the last extreme before start
        # so downstream charts can interpolate through "now"
        past = [e for e in extremes if e["time"] < start_utc]
        future = [e for e in extremes if start_utc <= e["time"] <= end_utc]
        output_extremes = (past[-1:] if past else []) + future

        return {
            "extremes": output_extremes,
            "hourly_heights": hourly_heights,
            "fetched_at": datetime.now(timezone.utc),
            "source": "station",
        }

    def _interpolate_height(
        self, extremes: list[dict[str, Any]], t: datetime
    ) -> Optional[float]:
        """Cosine-interpolate tide height at time t between extremes.

        Args:
            extremes: Sorted list of extreme dicts with time and height_m
            t: Target time

        Returns:
            Interpolated height, or None if t is outside extremes range
        """
        # Find bracketing extremes
        before = None
        after = None

        for i, ext in enumerate(extremes):
            if ext["time"] <= t:
                before = ext
            elif ext["time"] > t and after is None:
                after = ext
                break

        if before is None or after is None:
            return None

        # Cosine interpolation
        span = (after["time"] - before["time"]).total_seconds()
        if span <= 0:
            return before["height_m"]

        progress = (t - before["time"]).total_seconds() / span
        # Smooth cosine curve: 0→1 as progress goes 0→1
        t_smooth = (1.0 - math.cos(progress * math.pi)) / 2.0

        return before["height_m"] + (after["height_m"] - before["height_m"]) * t_smooth

    @staticmethod
    def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate great-circle distance in km between two points."""
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
