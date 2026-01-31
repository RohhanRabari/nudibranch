"""Tests for safety assessment system."""

import pytest

from nudibranch.models import SafetyLevel
from nudibranch.safety import SafetyAssessor


@pytest.fixture
def thresholds():
    """Standard safety thresholds for testing."""
    return {
        "wind_speed_kt": {"safe": 10, "caution": 15, "unsafe": 20},
        "wave_height_m": {"safe": 0.5, "caution": 1.0, "unsafe": 1.5},
        "swell_height_m": {"safe": 1.0, "caution": 1.5, "unsafe": 2.0},
        "swell_period_s": {"safe": 10, "caution": 7, "unsafe": 5},  # Higher is better
        "wind_gust_kt": {"safe": 15, "caution": 20, "unsafe": 25},
    }


@pytest.fixture
def assessor(thresholds):
    """Safety assessor instance."""
    return SafetyAssessor(thresholds)


def test_safe_conditions(assessor):
    """Test assessment of ideal safe conditions."""
    conditions = {
        "wind_speed_kt": 8.0,
        "wave_height_m": 0.3,
        "swell_height_m": 0.5,
        "swell_period_s": 12.0,
        "wind_gust_kt": 10.0,
    }

    result = assessor.assess_conditions(conditions)

    assert result["overall"] == SafetyLevel.SAFE
    assert all(f["status"] == SafetyLevel.SAFE for f in result["factors"].values())
    assert result["limiting_factor"] is None
    assert "safe" in result["details"].lower()


def test_caution_wind(assessor):
    """Test caution level due to wind."""
    conditions = {
        "wind_speed_kt": 12.0,  # Between 10-15 = CAUTION
        "wave_height_m": 0.4,
        "swell_period_s": 11.0,
    }

    result = assessor.assess_conditions(conditions)

    assert result["overall"] == SafetyLevel.CAUTION
    assert result["factors"]["wind"]["status"] == SafetyLevel.CAUTION
    assert result["limiting_factor"] == "wind"


def test_unsafe_waves(assessor):
    """Test unsafe level due to high waves."""
    conditions = {
        "wind_speed_kt": 8.0,
        "wave_height_m": 0.8,  # Between 0.5-1.0 = CAUTION
        "swell_height_m": 0.5,
    }

    # Waves at 0.8m should be CAUTION
    result = assessor.assess_conditions(conditions)
    assert result["overall"] == SafetyLevel.CAUTION
    assert result["factors"]["waves"]["status"] == SafetyLevel.CAUTION

    # Waves above 1.0m should be UNSAFE
    conditions["wave_height_m"] = 1.2
    result = assessor.assess_conditions(conditions)
    assert result["overall"] == SafetyLevel.UNSAFE
    assert result["factors"]["waves"]["status"] == SafetyLevel.UNSAFE
    assert result["limiting_factor"] == "waves"


def test_swell_period_assessment(assessor):
    """Test swell period assessment (higher is better)."""
    conditions = {
        "wind_speed_kt": 8.0,
        "wave_height_m": 0.4,
        "swell_period_s": 11.0,  # >10 = SAFE
    }

    result = assessor.assess_conditions(conditions)
    assert result["factors"]["swell_period"]["status"] == SafetyLevel.SAFE

    # Moderate period
    conditions["swell_period_s"] = 8.0  # 7-10 = CAUTION
    result = assessor.assess_conditions(conditions)
    assert result["factors"]["swell_period"]["status"] == SafetyLevel.CAUTION

    # Short period (choppy)
    conditions["swell_period_s"] = 5.0  # <7 = UNSAFE
    result = assessor.assess_conditions(conditions)
    assert result["factors"]["swell_period"]["status"] == SafetyLevel.UNSAFE


def test_multiple_caution_factors(assessor):
    """Test with multiple factors in caution range."""
    conditions = {
        "wind_speed_kt": 12.0,  # CAUTION
        "wave_height_m": 0.8,  # CAUTION
        "wind_gust_kt": 18.0,  # CAUTION
    }

    result = assessor.assess_conditions(conditions)

    assert result["overall"] == SafetyLevel.CAUTION
    assert result["factors"]["wind"]["status"] == SafetyLevel.CAUTION
    assert result["factors"]["waves"]["status"] == SafetyLevel.CAUTION
    assert result["factors"]["gusts"]["status"] == SafetyLevel.CAUTION
    assert result["limiting_factor"] in ["wind", "waves", "gusts"]


def test_mixed_safe_and_unsafe(assessor):
    """Test with mix of safe and unsafe conditions."""
    conditions = {
        "wind_speed_kt": 5.0,  # SAFE
        "wave_height_m": 0.3,  # SAFE
        "swell_height_m": 2.5,  # UNSAFE (>2.0)
    }

    result = assessor.assess_conditions(conditions)

    # Overall should be UNSAFE (worst case)
    assert result["overall"] == SafetyLevel.UNSAFE
    assert result["factors"]["wind"]["status"] == SafetyLevel.SAFE
    assert result["factors"]["waves"]["status"] == SafetyLevel.SAFE
    assert result["factors"]["swell"]["status"] == SafetyLevel.UNSAFE
    assert result["limiting_factor"] == "swell"


def test_missing_optional_fields(assessor):
    """Test with only required fields."""
    conditions = {
        "wind_speed_kt": 8.0,
        "wave_height_m": 0.4,
        # No swell data, no gusts
    }

    result = assessor.assess_conditions(conditions)

    assert result["overall"] == SafetyLevel.SAFE
    assert "wind" in result["factors"]
    assert "waves" in result["factors"]
    assert "swell" not in result["factors"]
    assert "gusts" not in result["factors"]


def test_none_values_ignored(assessor):
    """Test that None values are properly ignored."""
    conditions = {
        "wind_speed_kt": 8.0,
        "wave_height_m": 0.4,
        "swell_height_m": None,  # Should be ignored
        "wind_gust_kt": None,  # Should be ignored
    }

    result = assessor.assess_conditions(conditions)

    assert "swell" not in result["factors"]
    assert "gusts" not in result["factors"]
    assert result["overall"] == SafetyLevel.SAFE


def test_details_generation(assessor):
    """Test human-readable details generation."""
    # All safe
    conditions = {"wind_speed_kt": 5.0, "wave_height_m": 0.3}
    result = assessor.assess_conditions(conditions)
    assert "safe" in result["details"].lower()

    # Caution
    conditions = {"wind_speed_kt": 12.0, "wave_height_m": 0.3}
    result = assessor.assess_conditions(conditions)
    assert "wind" in result["details"].lower()
    assert "caution" in result["details"].lower()

    # Unsafe
    conditions = {"wind_speed_kt": 5.0, "wave_height_m": 1.8}
    result = assessor.assess_conditions(conditions)
    assert "unsafe" in result["details"].lower()
    assert "waves" in result["details"].lower()


def test_empty_conditions(assessor):
    """Test with no conditions provided."""
    result = assessor.assess_conditions({})

    assert result["overall"] == SafetyLevel.SAFE
    assert result["factors"] == {}
    assert result["limiting_factor"] is None
