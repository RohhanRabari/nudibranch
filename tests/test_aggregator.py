"""Tests for conditions aggregator."""

import re
from datetime import datetime, timedelta

import pytest
from pytest_httpx import HTTPXMock

from nudibranch.aggregator import ConditionsAggregator
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient
from nudibranch.models import DiveSpot
from nudibranch.safety import SafetyAssessor
from nudibranch.visibility import VisibilityEstimator


@pytest.fixture
def test_spot():
    """Test dive spot."""
    return DiveSpot(
        name="Test Spot",
        lat=7.6,
        lng=98.37,
        region="Test Region",
        depth_range="10-30m",
    )


@pytest.fixture
def thresholds():
    """Test thresholds."""
    return {
        "wind_speed_kt": {"safe": 10, "caution": 15, "unsafe": 20},
        "wave_height_m": {"safe": 0.5, "caution": 1.0, "unsafe": 1.5},
        "swell_height_m": {"safe": 1.0, "caution": 1.5, "unsafe": 2.0},
        "swell_period_s": {"safe": 10, "caution": 7, "unsafe": 5},
        "visibility": {
            "turbidity_fnu": {"good": 2.0, "poor": 5.0},
            "rainfall_mm_3day": {"good": 10, "poor": 50},
            "wind_avg_kt_5day": {"good": 8, "poor": 15},
        },
    }


@pytest.fixture
def mock_tide_responses(httpx_mock: HTTPXMock):
    """Mock Stormglass API responses for tide data."""
    now = datetime.now()

    # Mock extremes response
    extremes_response = {
        "data": [
            {"time": (now + timedelta(hours=3)).isoformat() + "Z", "height": 2.1, "type": "high"},
            {"time": (now + timedelta(hours=9)).isoformat() + "Z", "height": 0.3, "type": "low"},
            {"time": (now + timedelta(hours=15)).isoformat() + "Z", "height": 2.3, "type": "high"},
            {"time": (now + timedelta(hours=21)).isoformat() + "Z", "height": 0.5, "type": "low"},
        ]
    }

    # Mock sea-level response
    sealevel_data = []
    for hour in range(24):
        height = 1.2 + 0.9 * (1 if hour % 12 < 6 else -1)
        sealevel_data.append({
            "time": (now + timedelta(hours=hour)).isoformat() + "Z",
            "sg": height
        })
    sealevel_response = {"data": sealevel_data}

    # Add multiple mocks for multiple test calls
    for _ in range(10):  # Enough for all aggregator tests
        httpx_mock.add_response(
            url=re.compile(r"https://api\.stormglass\.io/v2/tide/extremes/point.*"),
            json=extremes_response,
        )
        httpx_mock.add_response(
            url=re.compile(r"https://api\.stormglass\.io/v2/tide/sea-level/point.*"),
            json=sealevel_response,
        )


@pytest.mark.asyncio
async def test_aggregator_initialization():
    """Test aggregator can be initialized."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient()

    aggregator = ConditionsAggregator(
        open_meteo=open_meteo,
        tide_client=tide_client,
    )

    assert aggregator.open_meteo is open_meteo
    assert aggregator.tide_client is tide_client
    assert aggregator.copernicus is None
    assert aggregator.safety_assessor is None
    assert aggregator.visibility_estimator is None


@pytest.mark.asyncio
async def test_fetch_spot_conditions_basic(test_spot, thresholds, mock_tide_responses):
    """Test fetching spot conditions with all components."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient(api_key="test_api_key")  # Use test API key
    safety_assessor = SafetyAssessor(thresholds)
    visibility_estimator = VisibilityEstimator(thresholds)

    aggregator = ConditionsAggregator(
        open_meteo=open_meteo,
        tide_client=tide_client,
        safety_assessor=safety_assessor,
        visibility_estimator=visibility_estimator,
    )

    # This will make real API calls to Open-Meteo
    conditions = await aggregator.fetch_spot_conditions(test_spot)

    # Check basic structure
    assert conditions.spot == test_spot
    assert conditions.marine is not None
    assert conditions.tides is not None
    assert conditions.safety is not None
    assert conditions.visibility is not None
    assert conditions.metadata is not None

    # Check marine data
    assert conditions.marine.wind_speed_kt >= 0
    assert conditions.marine.wave_height_m >= 0

    # Check tide data
    assert len(conditions.tides.extremes) > 0
    assert conditions.tides.current_height_m is not None
    assert conditions.tides.is_rising is not None

    # Check metadata
    assert "cache_status" in conditions.metadata
    assert conditions.metadata["cache_status"]["marine"] == "fetched"
    assert conditions.metadata["cache_status"]["tides"] == "fetched"


@pytest.mark.asyncio
async def test_fetch_without_optional_components(test_spot, mock_tide_responses):
    """Test fetching without safety/visibility estimators."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient(api_key="test_api_key")  # Use test API key

    aggregator = ConditionsAggregator(
        open_meteo=open_meteo,
        tide_client=tide_client,
    )

    conditions = await aggregator.fetch_spot_conditions(test_spot)

    assert conditions.marine is not None
    assert conditions.tides is not None
    assert conditions.safety is None  # Not provided
    assert conditions.visibility is None  # Not provided


@pytest.mark.asyncio
async def test_metadata_tracking(test_spot, thresholds, mock_tide_responses):
    """Test that metadata tracks fetch status."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient(api_key="test_api_key")  # Use test API key
    safety_assessor = SafetyAssessor(thresholds)
    visibility_estimator = VisibilityEstimator(thresholds)

    aggregator = ConditionsAggregator(
        open_meteo=open_meteo,
        tide_client=tide_client,
        safety_assessor=safety_assessor,
        visibility_estimator=visibility_estimator,
    )

    conditions = await aggregator.fetch_spot_conditions(test_spot)

    # Check cache status
    assert "cache_status" in conditions.metadata
    assert "marine" in conditions.metadata["cache_status"]
    assert "tides" in conditions.metadata["cache_status"]

    # Check derived fields
    assert "wind_speed_beaufort" in conditions.metadata
    assert 0 <= conditions.metadata["wind_speed_beaufort"] <= 12

    # Should have time to next high
    if conditions.tides.next_high:
        assert "time_to_next_high_minutes" in conditions.metadata


def test_wind_to_beaufort():
    """Test Beaufort scale conversion."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient()
    aggregator = ConditionsAggregator(open_meteo, tide_client)

    # Test various wind speeds
    assert aggregator._wind_to_beaufort(0) == 0  # Calm
    assert aggregator._wind_to_beaufort(3) == 1  # Light air
    assert aggregator._wind_to_beaufort(6) == 2  # Light breeze
    assert aggregator._wind_to_beaufort(10) == 3  # Gentle breeze
    assert aggregator._wind_to_beaufort(15) == 4  # Moderate breeze
    assert aggregator._wind_to_beaufort(21) == 5  # Fresh breeze
    assert aggregator._wind_to_beaufort(27) == 6  # Strong breeze
    assert aggregator._wind_to_beaufort(40) == 8  # Gale
    assert aggregator._wind_to_beaufort(70) == 12  # Hurricane


def test_estimate_current_tide():
    """Test current tide estimation."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient()
    aggregator = ConditionsAggregator(open_meteo, tide_client)

    now = datetime(2024, 1, 1, 12, 0, 0)
    hourly_heights = [
        (datetime(2024, 1, 1, 11, 0, 0), 1.0),
        (datetime(2024, 1, 1, 12, 0, 0), 1.5),
        (datetime(2024, 1, 1, 13, 0, 0), 2.0),
    ]

    # Exact match
    height, is_rising = aggregator._estimate_current_tide(hourly_heights, now)
    assert height == 1.5
    assert is_rising is True

    # Between points (rising tide)
    now = datetime(2024, 1, 1, 11, 30, 0)
    height, is_rising = aggregator._estimate_current_tide(hourly_heights, now)
    assert 1.0 < height < 1.5  # Interpolated
    assert is_rising is True

    # Falling tide
    hourly_heights = [
        (datetime(2024, 1, 1, 11, 0, 0), 2.0),
        (datetime(2024, 1, 1, 12, 0, 0), 1.5),
        (datetime(2024, 1, 1, 13, 0, 0), 1.0),
    ]
    height, is_rising = aggregator._estimate_current_tide(hourly_heights, now)
    assert is_rising is False


def test_estimate_current_tide_edge_cases():
    """Test edge cases in tide estimation."""
    open_meteo = OpenMeteoClient()
    tide_client = TideClient()
    aggregator = ConditionsAggregator(open_meteo, tide_client)

    # Empty list
    height, is_rising = aggregator._estimate_current_tide([], datetime.now())
    assert height is None
    assert is_rising is None

    # Single point
    now = datetime.now()
    hourly_heights = [(now, 1.5)]
    height, is_rising = aggregator._estimate_current_tide(hourly_heights, now)
    assert height == 1.5
    assert is_rising is None
