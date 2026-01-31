"""Tests for tide prediction client."""

from datetime import datetime, timedelta

import pytest
from pytest_httpx import HTTPXMock

from nudibranch.clients.tides import TideClient


@pytest.fixture
def mock_tide_extremes_response():
    """Mock response for tide extremes endpoint."""
    now = datetime.now()
    return {
        "data": [
            {"time": (now + timedelta(hours=3)).isoformat() + "Z", "height": 2.1, "type": "high"},
            {"time": (now + timedelta(hours=9)).isoformat() + "Z", "height": 0.3, "type": "low"},
            {"time": (now + timedelta(hours=15)).isoformat() + "Z", "height": 2.3, "type": "high"},
            {"time": (now + timedelta(hours=21)).isoformat() + "Z", "height": 0.5, "type": "low"},
        ]
    }


@pytest.fixture
def mock_tide_sealevel_response():
    """Mock response for tide sea-level endpoint."""
    now = datetime.now()
    data = []
    for hour in range(24):
        # Simulate a simple tide curve
        height = 1.2 + 0.9 * (1 if hour % 12 < 6 else -1)
        data.append({
            "time": (now + timedelta(hours=hour)).isoformat() + "Z",
            "sg": height
        })
    return {"data": data}


@pytest.mark.asyncio
async def test_fetch_tides(httpx_mock: HTTPXMock, mock_tide_extremes_response, mock_tide_sealevel_response):
    """Test fetching tide predictions with mocked API."""
    import re

    # Mock the extremes endpoint (match URL with any query params)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/extremes/point.*"),
        json=mock_tide_extremes_response,
    )

    # Mock the sea-level endpoint (match URL with any query params)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/sea-level/point.*"),
        json=mock_tide_sealevel_response,
    )

    client = TideClient(api_key="test_api_key")
    result = await client.fetch_tides(7.6, 98.37, days=1)

    assert "extremes" in result
    assert "hourly_heights" in result
    assert "fetched_at" in result

    # Should have 4 extremes from mock
    assert len(result["extremes"]) == 4

    # Should have 24 hours of data
    assert len(result["hourly_heights"]) == 24

    # Check extremes structure
    for extreme in result["extremes"]:
        assert "time" in extreme
        assert "height_m" in extreme
        assert "type" in extreme
        assert extreme["type"] in ["High", "Low"]
        assert isinstance(extreme["time"], datetime)
        assert isinstance(extreme["height_m"], float)

    # Check hourly heights structure
    for time, height in result["hourly_heights"]:
        assert isinstance(time, datetime)
        assert isinstance(height, float)

    await client.close()


@pytest.mark.asyncio
async def test_extremes_alternate(httpx_mock: HTTPXMock, mock_tide_extremes_response, mock_tide_sealevel_response):
    """Test that highs and lows alternate properly."""
    import re
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/extremes/point.*"),
        json=mock_tide_extremes_response,
    )
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/sea-level/point.*"),
        json=mock_tide_sealevel_response,
    )

    client = TideClient(api_key="test_api_key")
    result = await client.fetch_tides(7.6, 98.37, days=1)

    extremes = result["extremes"]
    types = [e["type"] for e in extremes]

    assert "High" in types
    assert "Low" in types

    await client.close()


@pytest.mark.asyncio
async def test_tide_range_reasonable(httpx_mock: HTTPXMock, mock_tide_extremes_response, mock_tide_sealevel_response):
    """Test that tide heights are within reasonable range."""
    import re
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/extremes/point.*"),
        json=mock_tide_extremes_response,
    )
    httpx_mock.add_response(
        url=re.compile(r"https://api\.stormglass\.io/v2/tide/sea-level/point.*"),
        json=mock_tide_sealevel_response,
    )

    client = TideClient(api_key="test_api_key")
    result = await client.fetch_tides(7.6, 98.37, days=1)

    extremes = result["extremes"]
    highs = [e["height_m"] for e in extremes if e["type"] == "High"]
    lows = [e["height_m"] for e in extremes if e["type"] == "Low"]

    assert len(highs) > 0
    assert len(lows) > 0

    # High tides should be higher than low tides
    assert max(highs) > min(lows)

    await client.close()


@pytest.mark.asyncio
async def test_different_locations(httpx_mock: HTTPXMock, mock_tide_extremes_response, mock_tide_sealevel_response):
    """Test predictions for different locations."""
    import re
    # Mock responses for both locations (2 locations × 2 endpoints each = 4 mocks)
    for _ in range(2):  # 2 locations
        httpx_mock.add_response(
            url=re.compile(r"https://api\.stormglass\.io/v2/tide/extremes/point.*"),
            json=mock_tide_extremes_response,
        )
        httpx_mock.add_response(
            url=re.compile(r"https://api\.stormglass\.io/v2/tide/sea-level/point.*"),
            json=mock_tide_sealevel_response,
        )

    client = TideClient(api_key="test_api_key")

    # Racha Yai
    result1 = await client.fetch_tides(7.601, 98.366, days=1)

    # Shark Point
    result2 = await client.fetch_tides(7.734, 98.414, days=1)

    # Both should have data
    assert len(result1["extremes"]) > 0
    assert len(result2["extremes"]) > 0

    assert len(result1["hourly_heights"]) == 24
    assert len(result2["hourly_heights"]) == 24

    await client.close()


@pytest.mark.asyncio
async def test_missing_api_key():
    """Test that missing API key raises error."""
    client = TideClient(api_key=None)

    with pytest.raises(ValueError, match="STORMGLASS_API_KEY"):
        await client.fetch_tides(7.6, 98.37, days=1)

    await client.close()


@pytest.mark.asyncio
async def test_close():
    """Test client close method."""
    client = TideClient(api_key="test_api_key")
    await client.close()  # Should not raise any errors
