"""Tests for visibility estimation system."""

import pytest

from nudibranch.models import VisibilityLevel
from nudibranch.visibility import VisibilityEstimator


@pytest.fixture
def thresholds():
    """Standard visibility thresholds for testing."""
    return {
        "visibility": {
            "turbidity_fnu": {"good": 2.0, "poor": 5.0},
            "rainfall_mm_3day": {"good": 10, "poor": 50},
            "wind_avg_kt_5day": {"good": 8, "poor": 15},
        }
    }


@pytest.fixture
def estimator(thresholds):
    """Visibility estimator instance."""
    return VisibilityEstimator(thresholds)


def test_excellent_conditions(estimator):
    """Test estimation with ideal conditions."""
    result = estimator.estimate_visibility(
        turbidity_fnu=1.0,  # Low turbidity
        recent_rainfall_mm=0.0,  # No rain
        avg_wind_speed_kt=5.0,  # Calm
        swell_height_m=0.3,  # Flat seas
    )

    assert result["level"] == VisibilityLevel.GOOD
    assert result["range_estimate"] == "20-30m"
    assert result["confidence"] == "high"
    assert all(ind["status"] == "favorable" for ind in result["indicators"].values())


def test_poor_conditions(estimator):
    """Test estimation with poor conditions."""
    result = estimator.estimate_visibility(
        turbidity_fnu=8.0,  # High turbidity
        recent_rainfall_mm=80.0,  # Heavy rain
        avg_wind_speed_kt=20.0,  # Strong wind
        swell_height_m=2.0,  # Rough seas
    )

    assert result["level"] == VisibilityLevel.POOR
    assert result["range_estimate"] == "<10m"
    assert all(ind["status"] == "unfavorable" for ind in result["indicators"].values())


def test_mixed_conditions(estimator):
    """Test estimation with mixed conditions."""
    result = estimator.estimate_visibility(
        turbidity_fnu=3.0,  # Moderate
        recent_rainfall_mm=25.0,  # Some rain
        avg_wind_speed_kt=10.0,  # Moderate wind
        swell_height_m=1.0,  # Moderate swell
    )

    assert result["level"] == VisibilityLevel.MIXED
    assert result["range_estimate"] == "10-20m"


def test_no_turbidity_data(estimator):
    """Test estimation without satellite turbidity data."""
    result = estimator.estimate_visibility(
        turbidity_fnu=None,  # No satellite data
        recent_rainfall_mm=5.0,
        avg_wind_speed_kt=6.0,
        swell_height_m=0.4,
    )

    # Should still work with proxy data
    assert result["level"] in [VisibilityLevel.GOOD, VisibilityLevel.MIXED]
    assert "turbidity" not in result["indicators"]
    assert "No satellite turbidity data" in result["notes"]
    # Confidence should be lower without turbidity
    assert result["confidence"] in ["medium", "low"]


def test_confidence_levels(estimator):
    """Test confidence level calculation."""
    # High confidence: turbidity + favorable conditions
    result = estimator.estimate_visibility(
        turbidity_fnu=1.0,
        recent_rainfall_mm=0.0,
        avg_wind_speed_kt=5.0,
        swell_height_m=0.3,
    )
    assert result["confidence"] == "high"

    # Medium confidence: turbidity + mixed conditions
    result = estimator.estimate_visibility(
        turbidity_fnu=3.0,
        recent_rainfall_mm=30.0,
        avg_wind_speed_kt=12.0,
        swell_height_m=1.2,
    )
    assert result["confidence"] == "medium"

    # Medium confidence: no turbidity but favorable conditions
    result = estimator.estimate_visibility(
        turbidity_fnu=None,
        recent_rainfall_mm=2.0,
        avg_wind_speed_kt=4.0,
        swell_height_m=0.2,
    )
    assert result["confidence"] == "medium"

    # Low confidence: no turbidity + poor conditions
    result = estimator.estimate_visibility(
        turbidity_fnu=None,
        recent_rainfall_mm=60.0,
        avg_wind_speed_kt=18.0,
        swell_height_m=2.0,
    )
    assert result["confidence"] == "low"


def test_individual_indicators(estimator):
    """Test individual indicator assessments."""
    result = estimator.estimate_visibility(
        turbidity_fnu=1.5,
        recent_rainfall_mm=5.0,
        avg_wind_speed_kt=7.0,
        swell_height_m=0.4,
    )

    # Check all indicators are present
    assert "turbidity" in result["indicators"]
    assert "rainfall" in result["indicators"]
    assert "wind" in result["indicators"]
    assert "swell" in result["indicators"]

    # Check indicator structure
    for indicator in result["indicators"].values():
        assert "value" in indicator
        assert "status" in indicator
        assert "score" in indicator
        assert "message" in indicator


def test_turbidity_thresholds(estimator):
    """Test turbidity threshold boundaries."""
    # Good
    result = estimator.estimate_visibility(
        turbidity_fnu=1.5,  # Below 2.0
        recent_rainfall_mm=0.0,
        avg_wind_speed_kt=5.0,
        swell_height_m=0.3,
    )
    assert result["indicators"]["turbidity"]["status"] == "favorable"

    # Moderate
    result = estimator.estimate_visibility(
        turbidity_fnu=3.5,  # Between 2.0-5.0
        recent_rainfall_mm=0.0,
        avg_wind_speed_kt=5.0,
        swell_height_m=0.3,
    )
    assert result["indicators"]["turbidity"]["status"] == "moderate"

    # Poor
    result = estimator.estimate_visibility(
        turbidity_fnu=6.0,  # Above 5.0
        recent_rainfall_mm=0.0,
        avg_wind_speed_kt=5.0,
        swell_height_m=0.3,
    )
    assert result["indicators"]["turbidity"]["status"] == "unfavorable"


def test_rainfall_impact(estimator):
    """Test rainfall impact on visibility."""
    # Minimal rain - favorable
    result = estimator.estimate_visibility(
        recent_rainfall_mm=5.0, avg_wind_speed_kt=5.0, swell_height_m=0.3
    )
    assert result["indicators"]["rainfall"]["status"] == "favorable"

    # Moderate rain
    result = estimator.estimate_visibility(
        recent_rainfall_mm=30.0, avg_wind_speed_kt=5.0, swell_height_m=0.3
    )
    assert result["indicators"]["rainfall"]["status"] == "moderate"

    # Heavy rain - unfavorable
    result = estimator.estimate_visibility(
        recent_rainfall_mm=60.0, avg_wind_speed_kt=5.0, swell_height_m=0.3
    )
    assert result["indicators"]["rainfall"]["status"] == "unfavorable"


def test_wind_impact(estimator):
    """Test wind impact on visibility."""
    # Calm winds
    result = estimator.estimate_visibility(
        avg_wind_speed_kt=6.0, recent_rainfall_mm=0.0, swell_height_m=0.3
    )
    assert result["indicators"]["wind"]["status"] == "favorable"

    # Moderate winds
    result = estimator.estimate_visibility(
        avg_wind_speed_kt=12.0, recent_rainfall_mm=0.0, swell_height_m=0.3
    )
    assert result["indicators"]["wind"]["status"] == "moderate"

    # Strong winds
    result = estimator.estimate_visibility(
        avg_wind_speed_kt=18.0, recent_rainfall_mm=0.0, swell_height_m=0.3
    )
    assert result["indicators"]["wind"]["status"] == "unfavorable"


def test_notes_generation(estimator):
    """Test explanatory notes generation."""
    # With turbidity data
    result = estimator.estimate_visibility(
        turbidity_fnu=1.0, recent_rainfall_mm=0.0, avg_wind_speed_kt=5.0, swell_height_m=0.3
    )
    assert "not direct measurement" in result["notes"]
    assert "No satellite" not in result["notes"]

    # Without turbidity data
    result = estimator.estimate_visibility(
        turbidity_fnu=None, recent_rainfall_mm=0.0, avg_wind_speed_kt=5.0, swell_height_m=0.3
    )
    assert "No satellite turbidity data" in result["notes"]

    # Low confidence warning
    result = estimator.estimate_visibility(
        turbidity_fnu=None, recent_rainfall_mm=60.0, avg_wind_speed_kt=18.0, swell_height_m=2.0
    )
    assert "Low confidence" in result["notes"]
    assert "local dive reports" in result["notes"]
