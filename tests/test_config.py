"""Tests for configuration loading."""

import pytest
from nudibranch.config import Config
from nudibranch.models import DiveSpot


def test_config_loads_spots():
    """Test that configuration loads dive spots from YAML."""
    config = Config.load("config")

    assert len(config.spots) > 0
    assert all(isinstance(spot, DiveSpot) for spot in config.spots)


def test_config_loads_thresholds():
    """Test that configuration loads safety thresholds."""
    config = Config.load("config")

    assert "wind_speed_kt" in config.thresholds
    assert "wave_height_m" in config.thresholds
    assert "swell_period_s" in config.thresholds


def test_dive_spot_validation():
    """Test that DiveSpot model validates correctly."""
    spot = DiveSpot(
        name="Test Spot",
        lat=7.5,
        lng=98.5,
        region="Test Region",
        depth_range="10-30m"
    )

    assert spot.name == "Test Spot"
    assert spot.lat == 7.5
    assert spot.lng == 98.5


def test_dive_spot_invalid_coordinates():
    """Test that invalid coordinates are rejected."""
    with pytest.raises(Exception):
        DiveSpot(
            name="Invalid",
            lat=95.0,  # Invalid latitude
            lng=98.5,
            region="Test",
            depth_range="10m"
        )
