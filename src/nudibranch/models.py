"""Data models for marine conditions and dive spots."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DiveSpot(BaseModel):
    """Represents a dive location."""

    name: str = Field(description="Name of the dive spot")
    lat: float = Field(description="Latitude in decimal degrees", ge=-90, le=90)
    lng: float = Field(description="Longitude in decimal degrees", ge=-180, le=180)
    region: str = Field(description="Geographic region or area")
    depth_range: str = Field(description="Typical depth range (e.g., '5-40m')")
    description: Optional[str] = Field(default=None, description="Additional details about the spot")


class SafetyLevel(str, Enum):
    """Safety assessment levels for diving conditions."""

    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"


class VisibilityLevel(str, Enum):
    """Estimated underwater visibility ranges."""

    GOOD = "good"      # >20m
    MIXED = "mixed"    # 10-20m
    POOR = "poor"      # <10m


class MarineConditions(BaseModel):
    """Marine and weather conditions from Open-Meteo."""

    wave_height_m: float = Field(description="Significant wave height in meters")
    wave_period_s: Optional[float] = Field(default=None, description="Wave period in seconds")
    wave_direction_deg: Optional[float] = Field(default=None, description="Wave direction in degrees")

    swell_height_m: Optional[float] = Field(default=None, description="Swell height in meters")
    swell_period_s: Optional[float] = Field(default=None, description="Swell period in seconds")
    swell_direction_deg: Optional[float] = Field(default=None, description="Swell direction in degrees")

    wind_speed_kt: float = Field(description="Wind speed in knots")
    wind_direction_deg: Optional[float] = Field(default=None, description="Wind direction in degrees")
    wind_gust_kt: Optional[float] = Field(default=None, description="Wind gust speed in knots")

    temperature_c: Optional[float] = Field(default=None, description="Air temperature in Celsius")
    precipitation_mm: Optional[float] = Field(default=None, description="Precipitation in mm")
    cloud_cover_pct: Optional[int] = Field(default=None, description="Cloud cover percentage")

    fetched_at: datetime = Field(default_factory=datetime.now)


class TideExtreme(BaseModel):
    """Represents a high or low tide event."""

    time: datetime = Field(description="Time of the tide extreme")
    height_m: float = Field(description="Tide height in meters")
    type: str = Field(description="'high' or 'low'")


class TideConditions(BaseModel):
    """Tide information for a location."""

    extremes: list[TideExtreme] = Field(description="High and low tide times")
    current_height_m: Optional[float] = Field(default=None, description="Current tide height")
    is_rising: Optional[bool] = Field(default=None, description="Whether tide is rising")
    next_high: Optional[TideExtreme] = Field(default=None)
    next_low: Optional[TideExtreme] = Field(default=None)
    fetched_at: datetime = Field(default_factory=datetime.now)


class VisibilityEstimate(BaseModel):
    """Estimated visibility based on proxy indicators."""

    level: VisibilityLevel
    confidence: str = Field(description="'low', 'medium', or 'high'")
    range_estimate: str = Field(description="Estimated range (e.g., '20-30m')")
    indicators: dict[str, dict] = Field(description="Contributing factors and their status")
    notes: str = Field(default="Based on satellite and weather proxy - not measured")


class SafetyAssessment(BaseModel):
    """Safety evaluation of diving conditions."""

    overall: SafetyLevel
    factors: dict[str, dict] = Field(description="Individual factor assessments")
    limiting_factor: Optional[str] = Field(default=None, description="Most restrictive condition")


class FullConditions(BaseModel):
    """Complete conditions data for a dive spot."""

    spot: DiveSpot
    marine: Optional[MarineConditions] = None
    tides: Optional[TideConditions] = None
    visibility: Optional[VisibilityEstimate] = None
    safety: Optional[SafetyAssessment] = None
    metadata: dict = Field(default_factory=dict, description="Fetch status and cache info")
    fetched_at: datetime = Field(default_factory=datetime.now)
