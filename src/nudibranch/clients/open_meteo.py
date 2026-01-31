"""Open-Meteo API client for marine and weather data.

API Documentation:
- Marine: https://open-meteo.com/en/docs/marine-weather-api
- Weather: https://open-meteo.com/en/docs
"""

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class OpenMeteoClient:
    """Async client for Open-Meteo Marine and Weather APIs.

    Example:
        >>> async with OpenMeteoClient() as client:
        ...     marine = await client.fetch_marine(7.601, 98.366)
        ...     weather = await client.fetch_weather(7.601, 98.366)
    """

    MARINE_BASE_URL = "https://marine-api.open-meteo.com/v1/marine"
    WEATHER_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT = 30.0

    def __init__(self) -> None:
        """Initialize the Open-Meteo client."""
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OpenMeteoClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating it if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def fetch_marine(self, lat: float, lng: float) -> dict[str, Any]:
        """Fetch marine conditions from Open-Meteo Marine API.

        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees

        Returns:
            Dictionary containing:
                - wave_height_m: Significant wave height in meters
                - wave_period_s: Wave period in seconds
                - wave_direction_deg: Wave direction in degrees
                - swell_height_m: Swell height in meters
                - swell_period_s: Swell period in seconds
                - swell_direction_deg: Swell direction in degrees
                - timestamp: Time of observation

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": [
                "wave_height",
                "wave_period",
                "wave_direction",
                "swell_wave_height",
                "swell_wave_period",
                "swell_wave_direction",
            ],
            "timezone": "Asia/Bangkok",
        }

        response = await self.client.get(self.MARINE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})

        return {
            "wave_height_m": current.get("wave_height", 0.0),
            "wave_period_s": current.get("wave_period"),
            "wave_direction_deg": current.get("wave_direction"),
            "swell_height_m": current.get("swell_wave_height"),
            "swell_period_s": current.get("swell_wave_period"),
            "swell_direction_deg": current.get("swell_wave_direction"),
            "timestamp": datetime.fromisoformat(current.get("time", datetime.now().isoformat())),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def fetch_weather(self, lat: float, lng: float) -> dict[str, Any]:
        """Fetch weather conditions from Open-Meteo Weather API.

        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees

        Returns:
            Dictionary containing:
                - wind_speed_kt: Wind speed in knots (converted from km/h)
                - wind_direction_deg: Wind direction in degrees
                - wind_gust_kt: Wind gust speed in knots
                - precipitation_mm: Precipitation in mm
                - cloud_cover_pct: Cloud cover percentage
                - temperature_c: Air temperature in Celsius
                - timestamp: Time of observation

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": [
                "temperature_2m",
                "precipitation",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ],
            "timezone": "Asia/Bangkok",
            "wind_speed_unit": "kn",  # Request in knots directly
        }

        response = await self.client.get(self.WEATHER_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})

        return {
            "wind_speed_kt": current.get("wind_speed_10m", 0.0),
            "wind_direction_deg": current.get("wind_direction_10m"),
            "wind_gust_kt": current.get("wind_gusts_10m"),
            "precipitation_mm": current.get("precipitation", 0.0),
            "cloud_cover_pct": current.get("cloud_cover", 0),
            "temperature_c": current.get("temperature_2m"),
            "timestamp": datetime.fromisoformat(current.get("time", datetime.now().isoformat())),
        }

    async def fetch_combined(self, lat: float, lng: float) -> dict[str, Any]:
        """Fetch both marine and weather conditions.

        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees

        Returns:
            Combined dictionary with marine and weather data
        """
        marine = await self.fetch_marine(lat, lng)
        weather = await self.fetch_weather(lat, lng)

        return {**marine, **weather}

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
