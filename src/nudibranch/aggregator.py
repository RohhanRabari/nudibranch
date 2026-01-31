"""Data aggregator combining all API sources for comprehensive dive spot conditions.

Fetches data from multiple sources, handles failures gracefully, and provides
a unified view of current conditions including safety assessment and visibility estimation.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from nudibranch.clients.copernicus import CopernicusClient
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient
from nudibranch.models import DiveSpot, FullConditions, MarineConditions, TideConditions
from nudibranch.safety import SafetyAssessor
from nudibranch.visibility import VisibilityEstimator


class ConditionsAggregator:
    """Aggregates data from all sources to provide comprehensive dive conditions.

    Combines:
    - Marine weather (Open-Meteo)
    - Tide predictions (harmonic analysis)
    - Turbidity (Copernicus - optional)
    - Safety assessment
    - Visibility estimation
    """

    def __init__(
        self,
        open_meteo: OpenMeteoClient,
        tide_client: TideClient,
        copernicus: Optional[CopernicusClient] = None,
        safety_assessor: Optional[SafetyAssessor] = None,
        visibility_estimator: Optional[VisibilityEstimator] = None,
    ) -> None:
        """Initialize the aggregator.

        Args:
            open_meteo: Open-Meteo API client
            tide_client: Tide prediction client
            copernicus: Copernicus Marine client (optional)
            safety_assessor: Safety assessment engine (optional)
            visibility_estimator: Visibility estimation engine (optional)
        """
        self.open_meteo = open_meteo
        self.tide_client = tide_client
        self.copernicus = copernicus
        self.safety_assessor = safety_assessor
        self.visibility_estimator = visibility_estimator

    async def fetch_spot_conditions(self, spot: DiveSpot) -> FullConditions:
        """Fetch comprehensive conditions for a dive spot.

        Args:
            spot: Dive spot to fetch conditions for

        Returns:
            FullConditions object with all available data
        """
        metadata: dict[str, Any] = {"cache_status": {}, "errors": {}}

        # Fetch marine weather data
        marine_data = None
        try:
            marine_raw = await self.open_meteo.fetch_combined(spot.lat, spot.lng)
            marine_data = MarineConditions(
                wave_height_m=marine_raw["wave_height_m"],
                wave_period_s=marine_raw.get("wave_period_s"),
                wave_direction_deg=marine_raw.get("wave_direction_deg"),
                swell_height_m=marine_raw.get("swell_height_m"),
                swell_period_s=marine_raw.get("swell_period_s"),
                swell_direction_deg=marine_raw.get("swell_direction_deg"),
                wind_speed_kt=marine_raw["wind_speed_kt"],
                wind_direction_deg=marine_raw.get("wind_direction_deg"),
                wind_gust_kt=marine_raw.get("wind_gust_kt"),
                temperature_c=marine_raw.get("temperature_c"),
                precipitation_mm=marine_raw.get("precipitation_mm"),
                cloud_cover_pct=marine_raw.get("cloud_cover_pct"),
            )
            metadata["cache_status"]["marine"] = "fetched"
        except Exception as e:
            metadata["errors"]["marine"] = str(e)
            metadata["cache_status"]["marine"] = "failed"

        # Fetch tide predictions
        tide_data = None
        try:
            tide_raw = await self.tide_client.fetch_tides(spot.lat, spot.lng, days=7)

            # Find next high and low (use UTC to match tide data)
            from datetime import timezone
            now = datetime.now(timezone.utc)
            next_high = None
            next_low = None

            for extreme in tide_raw["extremes"]:
                if extreme["time"] > now:
                    if extreme["type"] == "High" and next_high is None:
                        next_high = extreme
                    elif extreme["type"] == "Low" and next_low is None:
                        next_low = extreme

                if next_high and next_low:
                    break

            # Estimate current tide height and direction
            current_height, is_rising = self._estimate_current_tide(
                tide_raw["hourly_heights"], now
            )

            # Convert to TideConditions
            from nudibranch.models import TideExtreme

            tide_data = TideConditions(
                extremes=[
                    TideExtreme(
                        time=e["time"], height_m=e["height_m"], type=e["type"]
                    )
                    for e in tide_raw["extremes"][:14]  # Next 7 days of extremes
                ],
                current_height_m=current_height,
                is_rising=is_rising,
                next_high=TideExtreme(**next_high) if next_high else None,
                next_low=TideExtreme(**next_low) if next_low else None,
            )
            metadata["cache_status"]["tides"] = "fetched"
        except Exception as e:
            metadata["errors"]["tides"] = str(e)
            metadata["cache_status"]["tides"] = "failed"

        # Fetch turbidity (optional)
        turbidity = None
        if self.copernicus:
            try:
                turbidity = await self.copernicus.fetch_turbidity(
                    spot.lat, spot.lng, days_back=7
                )
                metadata["cache_status"]["turbidity"] = (
                    "fetched" if turbidity is not None else "no_data"
                )
            except Exception as e:
                metadata["errors"]["turbidity"] = str(e)
                metadata["cache_status"]["turbidity"] = "failed"

        # Calculate safety assessment
        safety = None
        if self.safety_assessor and marine_data:
            try:
                conditions_dict = {
                    "wind_speed_kt": marine_data.wind_speed_kt,
                    "wave_height_m": marine_data.wave_height_m,
                    "swell_height_m": marine_data.swell_height_m,
                    "swell_period_s": marine_data.swell_period_s,
                    "wind_gust_kt": marine_data.wind_gust_kt,
                }
                safety = self.safety_assessor.assess_conditions(conditions_dict)
            except Exception as e:
                metadata["errors"]["safety"] = str(e)

        # Calculate visibility estimation
        visibility = None
        if self.visibility_estimator and marine_data:
            try:
                # Estimate 3-day rainfall (rough approximation from current)
                recent_rainfall = (marine_data.precipitation_mm or 0.0) * 3

                # Use current wind as proxy for 5-day average
                avg_wind = marine_data.wind_speed_kt

                visibility = self.visibility_estimator.estimate_visibility(
                    turbidity_fnu=turbidity,
                    recent_rainfall_mm=recent_rainfall,
                    avg_wind_speed_kt=avg_wind,
                    swell_height_m=marine_data.swell_height_m or 0.0,
                )
            except Exception as e:
                metadata["errors"]["visibility"] = str(e)

        # Calculate derived fields
        if tide_data and tide_data.next_high:
            from datetime import timezone
            time_to_high = tide_data.next_high.time - datetime.now(timezone.utc)
            metadata["time_to_next_high_minutes"] = int(time_to_high.total_seconds() / 60)

        if marine_data:
            metadata["wind_speed_beaufort"] = self._wind_to_beaufort(
                marine_data.wind_speed_kt
            )

        return FullConditions(
            spot=spot,
            marine=marine_data,
            tides=tide_data,
            visibility=visibility,
            safety=safety,
            metadata=metadata,
        )

    def _estimate_current_tide(
        self, hourly_heights: list[tuple[datetime, float]], now: datetime
    ) -> tuple[Optional[float], Optional[bool]]:
        """Estimate current tide height and direction.

        Args:
            hourly_heights: List of (time, height) tuples
            now: Current time

        Returns:
            Tuple of (current_height, is_rising)
        """
        if not hourly_heights:
            return None, None

        # Find closest time points
        before = None
        after = None

        for i, (time, height) in enumerate(hourly_heights):
            if time <= now:
                before = (time, height)
            elif time > now and after is None:
                after = (time, height)
                break

        if not before or not after:
            # Use closest available
            closest = min(hourly_heights, key=lambda x: abs((x[0] - now).total_seconds()))
            return closest[1], None

        # Interpolate current height
        time_diff = (after[0] - before[0]).total_seconds()
        time_offset = (now - before[0]).total_seconds()
        fraction = time_offset / time_diff if time_diff > 0 else 0

        current_height = before[1] + (after[1] - before[1]) * fraction

        # Determine if rising or falling
        is_rising = after[1] > before[1]

        return current_height, is_rising

    def _wind_to_beaufort(self, wind_kt: float) -> int:
        """Convert wind speed in knots to Beaufort scale.

        Args:
            wind_kt: Wind speed in knots

        Returns:
            Beaufort scale number (0-12)
        """
        if wind_kt < 1:
            return 0
        elif wind_kt < 4:
            return 1
        elif wind_kt < 7:
            return 2
        elif wind_kt < 11:
            return 3
        elif wind_kt < 16:
            return 4
        elif wind_kt < 22:
            return 5
        elif wind_kt < 28:
            return 6
        elif wind_kt < 34:
            return 7
        elif wind_kt < 41:
            return 8
        elif wind_kt < 48:
            return 9
        elif wind_kt < 56:
            return 10
        elif wind_kt < 64:
            return 11
        else:
            return 12
