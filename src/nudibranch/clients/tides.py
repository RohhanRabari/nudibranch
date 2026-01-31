"""Tide prediction client using Stormglass.io API with harmonic fallback.

Provides accurate tide predictions for any location worldwide using
Stormglass.io's global tide data network with 5,000+ stations.

Falls back to harmonic analysis if API is unavailable or rate limited.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import numpy as np
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class TideClient:
    """Global tide prediction using Stormglass.io API.

    Provides accurate tide data for any location worldwide.
    Requires STORMGLASS_API_KEY environment variable (free tier available).

    Example:
        >>> client = TideClient()
        >>> tides = await client.fetch_tides(7.601, 98.366, days=7)
    """

    BASE_URL = "https://api.stormglass.io/v2"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the tide prediction client.

        Args:
            api_key: Stormglass.io API key (optional, reads from env if not provided)
        """
        self.api_key = api_key or os.getenv("STORMGLASS_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_tides(self, lat: float, lng: float, days: int = 7) -> dict[str, Any]:
        """Fetch tide predictions for a location.

        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            days: Number of days to predict (default: 7)

        Returns:
            Dictionary containing:
                - extremes: List of high/low tide events with time, height, type
                - hourly_heights: List of (datetime, height) tuples
                - fetched_at: Timestamp of fetch
                - source: "api" or "harmonic" indicating data source

        Note:
            Falls back to harmonic analysis if API is unavailable.
        """
        # Try API first if key is available
        if self.api_key:
            try:
                result = await self._fetch_with_retry(lat, lng, days)
                result["source"] = "api"
                return result
            except Exception as e:
                # API failed, fall back to harmonic
                print(f"⚠️  Stormglass API failed ({type(e).__name__}), using harmonic fallback")

        # Fallback to harmonic analysis
        return await self._fetch_harmonic(lat, lng, days)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _fetch_with_retry(self, lat: float, lng: float, days: int) -> dict[str, Any]:
        """Internal method to fetch tides with retry logic."""

        # Calculate time range
        start = datetime.now()
        end = start + timedelta(days=days)

        # Format timestamps for API (ISO 8601)
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

        # Fetch tide extremes (high/low)
        extremes_url = f"{self.BASE_URL}/tide/extremes/point"
        params_extremes = {
            "lat": lat,
            "lng": lng,
            "start": start_str,
            "end": end_str,
        }

        headers = {"Authorization": self.api_key}

        response = await self.client.get(
            extremes_url, params=params_extremes, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Parse extremes
        extremes = []
        for extreme in data.get("data", []):
            extremes.append(
                {
                    "time": datetime.fromisoformat(extreme["time"].replace("Z", "+00:00")),
                    "height_m": extreme["height"],
                    "type": extreme["type"].capitalize(),
                }
            )

        # Fetch hourly tide heights
        sea_level_url = f"{self.BASE_URL}/tide/sea-level/point"
        params_sea_level = {
            "lat": lat,
            "lng": lng,
            "start": start_str,
            "end": end_str,
        }

        response = await self.client.get(
            sea_level_url, params=params_sea_level, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Parse hourly heights
        hourly_heights = []
        for entry in data.get("data", []):
            time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
            height = entry["sg"]  # Stormglass tide height in meters
            hourly_heights.append((time, float(height)))

        return {
            "extremes": extremes,
            "hourly_heights": hourly_heights,
            "fetched_at": datetime.now(),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    # Harmonic fallback methods
    async def _fetch_harmonic(self, lat: float, lng: float, days: int) -> dict[str, Any]:
        """Fetch tide predictions using harmonic analysis (fallback).

        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            days: Number of days to predict

        Returns:
            Dictionary with tide predictions from harmonic model
        """
        # Generate time array (hourly for next N days) - use UTC to match API
        from datetime import timezone
        start = datetime.now(timezone.utc)
        hours = days * 24
        times = [start + timedelta(hours=h) for h in range(hours)]

        # Convert to numpy array of timestamps
        timestamps = np.array([t.timestamp() for t in times])

        # Use simplified tidal constituents for quick prediction
        constituents = ["m2", "s2", "n2", "k2", "k1", "o1", "p1", "q1"]

        # Get amplitudes and phases for this location
        amplitudes = self._estimate_amplitudes(lat, lng, constituents)
        phases = self._estimate_phases(lat, lng, constituents)

        # Calculate tide heights using harmonic prediction
        heights = self._harmonic_predict(timestamps, constituents, amplitudes, phases, lat)

        # Find extremes (high and low tides)
        extremes = self._find_extremes(times, heights)

        # Create hourly heights list
        hourly_heights = [(t, float(h)) for t, h in zip(times, heights)]

        return {
            "extremes": extremes,
            "hourly_heights": hourly_heights,
            "fetched_at": datetime.now(),
            "source": "harmonic",
        }

    def _estimate_amplitudes(
        self, lat: float, lng: float, constituents: list[str]
    ) -> dict[str, float]:
        """Estimate tidal constituent amplitudes for location.

        Uses improved regional scaling based on global tidal patterns.
        """
        # Base amplitudes (meters) - global averages
        base_amplitudes = {
            "m2": 0.5,  # Principal lunar semidiurnal
            "s2": 0.2,  # Principal solar semidiurnal
            "n2": 0.1,  # Larger lunar elliptic semidiurnal
            "k2": 0.05,  # Lunisolar semidiurnal
            "k1": 0.3,  # Lunar diurnal
            "o1": 0.2,  # Lunar diurnal
            "p1": 0.1,  # Solar diurnal
            "q1": 0.05,  # Larger lunar elliptic diurnal
        }

        # Regional scaling factors based on latitude
        # Tropical regions (0-30°): higher tides
        # Temperate (30-60°): moderate
        # Polar (60-90°): lower
        abs_lat = abs(lat)
        if abs_lat < 30:
            lat_factor = 1.2  # Tropical boost
        elif abs_lat < 60:
            lat_factor = 1.0  # Normal
        else:
            lat_factor = 0.7  # Polar reduction

        # Apply scaling
        return {c: base_amplitudes.get(c, 0.1) * lat_factor for c in constituents}

    def _estimate_phases(
        self, lat: float, lng: float, constituents: list[str]
    ) -> dict[str, float]:
        """Estimate tidal constituent phases for location.

        Improved phase estimation based on longitude and latitude.
        """
        # Phase varies primarily with longitude
        # Each 15° longitude ≈ 1 hour time shift
        base_phases = {
            "m2": (lng / 15.0) * 30.0,  # Semidiurnal: 2 cycles/day
            "s2": (lng / 15.0) * 30.0 + 30,
            "n2": (lng / 15.0) * 30.0 - 15,
            "k2": (lng / 15.0) * 30.0 + 45,
            "k1": (lng / 15.0) * 15.0 + 20,  # Diurnal: 1 cycle/day
            "o1": (lng / 15.0) * 15.0 - 10,
            "p1": (lng / 15.0) * 15.0 + 30,
            "q1": (lng / 15.0) * 15.0 - 20,
        }

        return {c: np.deg2rad(base_phases.get(c, 0.0) % 360) for c in constituents}

    def _harmonic_predict(
        self,
        timestamps: np.ndarray,
        constituents: list[str],
        amplitudes: dict[str, float],
        phases: dict[str, float],
        lat: float,
    ) -> np.ndarray:
        """Predict tide heights using harmonic analysis.

        Formula: h(t) = MSL + Σ A_i * cos(ω_i * t - φ_i)
        """
        # Angular frequencies (degrees per hour)
        frequencies = {
            "m2": 28.984104,  # Principal lunar semidiurnal
            "s2": 30.0,       # Principal solar semidiurnal
            "n2": 28.439730,  # Larger lunar elliptic
            "k2": 30.082137,  # Lunisolar semidiurnal
            "k1": 15.041069,  # Lunar diurnal
            "o1": 13.943035,  # Lunar diurnal
            "p1": 14.958931,  # Solar diurnal
            "q1": 13.398661,  # Larger lunar elliptic diurnal
        }

        # Convert timestamps to hours since epoch
        hours = timestamps / 3600.0

        # Calculate tide height as sum of constituents
        tide = np.zeros_like(hours)

        for const in constituents:
            amp = amplitudes[const]
            phase = phases[const]
            freq = np.deg2rad(frequencies[const])

            # h(t) = A * cos(ω*t - φ)
            tide += amp * np.cos(freq * hours - phase)

        # Add mean sea level offset (varies by region)
        # Estimate MSL based on latitude
        abs_lat = abs(lat)
        if abs_lat < 30:
            msl = 1.5  # Tropical oceans
        elif abs_lat < 60:
            msl = 1.0  # Temperate
        else:
            msl = 0.5  # Polar

        tide += msl

        return tide

    def _find_extremes(
        self, times: list[datetime], heights: np.ndarray
    ) -> list[dict[str, Any]]:
        """Find high and low tide times from height data."""
        extremes = []

        # Find local maxima and minima
        for i in range(1, len(heights) - 1):
            # Local maximum (high tide)
            if heights[i] > heights[i - 1] and heights[i] > heights[i + 1]:
                extremes.append(
                    {
                        "time": times[i],
                        "height_m": float(heights[i]),
                        "type": "High",
                    }
                )
            # Local minimum (low tide)
            elif heights[i] < heights[i - 1] and heights[i] < heights[i + 1]:
                extremes.append(
                    {
                        "time": times[i],
                        "height_m": float(heights[i]),
                        "type": "Low",
                    }
                )

        return extremes
