"""Tests for Open-Meteo API client."""

import re
from datetime import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock

from nudibranch.clients.open_meteo import OpenMeteoClient


@pytest.fixture
def marine_response():
    """Mock response for marine API."""
    return {
        "latitude": 7.6,
        "longitude": 98.37,
        "current": {
            "time": "2024-01-15T10:00",
            "wave_height": 0.8,
            "wave_period": 6.5,
            "wave_direction": 180,
            "swell_wave_height": 0.6,
            "swell_wave_period": 10.0,
            "swell_wave_direction": 190,
        },
    }


@pytest.fixture
def weather_response():
    """Mock response for weather API."""
    return {
        "latitude": 7.6,
        "longitude": 98.37,
        "current": {
            "time": "2024-01-15T10:00",
            "temperature_2m": 28.5,
            "precipitation": 0.0,
            "cloud_cover": 25,
            "wind_speed_10m": 12.0,
            "wind_direction_10m": 45,
            "wind_gusts_10m": 15.0,
        },
    }


@pytest.mark.asyncio
async def test_fetch_marine(httpx_mock: HTTPXMock, marine_response):
    """Test fetching marine conditions."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"https://marine-api\.open-meteo\.com/v1/marine\?.*"),
        json=marine_response,
    )

    async with OpenMeteoClient() as client:
        result = await client.fetch_marine(7.6, 98.37)

    assert result["wave_height_m"] == 0.8
    assert result["wave_period_s"] == 6.5
    assert result["wave_direction_deg"] == 180
    assert result["swell_height_m"] == 0.6
    assert result["swell_period_s"] == 10.0
    assert result["swell_direction_deg"] == 190
    assert isinstance(result["timestamp"], datetime)


@pytest.mark.asyncio
async def test_fetch_weather(httpx_mock: HTTPXMock, weather_response):
    """Test fetching weather conditions."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"https://api\.open-meteo\.com/v1/forecast\?.*"),
        json=weather_response,
    )

    async with OpenMeteoClient() as client:
        result = await client.fetch_weather(7.6, 98.37)

    assert result["wind_speed_kt"] == 12.0
    assert result["wind_direction_deg"] == 45
    assert result["wind_gust_kt"] == 15.0
    assert result["precipitation_mm"] == 0.0
    assert result["cloud_cover_pct"] == 25
    assert result["temperature_c"] == 28.5
    assert isinstance(result["timestamp"], datetime)


@pytest.mark.asyncio
async def test_fetch_combined(httpx_mock: HTTPXMock, marine_response, weather_response):
    """Test fetching combined marine and weather data."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"https://marine-api\.open-meteo\.com/v1/marine\?.*"),
        json=marine_response,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"https://api\.open-meteo\.com/v1/forecast\?.*"),
        json=weather_response,
    )

    async with OpenMeteoClient() as client:
        result = await client.fetch_combined(7.6, 98.37)

    # Check marine data
    assert result["wave_height_m"] == 0.8
    assert result["swell_height_m"] == 0.6

    # Check weather data
    assert result["wind_speed_kt"] == 12.0
    assert result["temperature_c"] == 28.5


@pytest.mark.asyncio
async def test_http_error_retry(httpx_mock: HTTPXMock, marine_response):
    """Test that HTTP errors trigger retries."""
    # First two attempts fail, third succeeds
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(json=marine_response)

    async with OpenMeteoClient() as client:
        result = await client.fetch_marine(7.6, 98.37)

    assert result["wave_height_m"] == 0.8
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_http_error_exhausted(httpx_mock: HTTPXMock):
    """Test that errors are raised after max retries."""
    # All attempts fail
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)

    async with OpenMeteoClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.fetch_marine(7.6, 98.37)


@pytest.mark.asyncio
async def test_context_manager():
    """Test that context manager properly handles client lifecycle."""
    async with OpenMeteoClient() as client:
        assert client._client is not None

    # Client should be closed after context exit
    # Note: we can't directly test if it's closed, but we verify no errors occur


@pytest.mark.asyncio
async def test_missing_optional_fields(httpx_mock: HTTPXMock):
    """Test handling of missing optional fields in response."""
    minimal_response = {
        "latitude": 7.6,
        "longitude": 98.37,
        "current": {
            "time": "2024-01-15T10:00",
            "wave_height": 0.5,
            # Missing optional fields
        },
    }

    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"https://marine-api\.open-meteo\.com/v1/marine\?.*"),
        json=minimal_response,
    )

    async with OpenMeteoClient() as client:
        result = await client.fetch_marine(7.6, 98.37)

    assert result["wave_height_m"] == 0.5
    assert result["wave_period_s"] is None
    assert result["swell_height_m"] is None
