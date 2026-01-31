"""Underwater visibility estimation using proxy indicators.

Estimates visibility based on turbidity (satellite), rainfall, wind, and sea state.
This is an estimation tool - not a replacement for actual visibility measurements.
"""

from typing import Any, Optional

from nudibranch.models import VisibilityLevel


class VisibilityEstimator:
    """Estimates underwater visibility using multiple proxy indicators.

    Uses a combination of:
    - Turbidity (satellite ocean color data) - if available
    - Recent rainfall (runoff affects visibility)
    - Average wind speed (churns up sediment)
    - Swell height (sea state)

    Note: This is an estimation based on proxy data, not direct measurement.
    """

    def __init__(self, thresholds: dict[str, Any]) -> None:
        """Initialize the visibility estimator.

        Args:
            thresholds: Threshold configuration from config file
        """
        self.thresholds = thresholds.get("visibility", {})

    def estimate_visibility(
        self,
        turbidity_fnu: Optional[float] = None,
        recent_rainfall_mm: float = 0.0,
        avg_wind_speed_kt: float = 0.0,
        swell_height_m: float = 0.0,
    ) -> dict[str, Any]:
        """Estimate underwater visibility from proxy indicators.

        Args:
            turbidity_fnu: Satellite turbidity in FNU (optional)
            recent_rainfall_mm: Rainfall in last 3 days (mm)
            avg_wind_speed_kt: 5-day rolling average wind speed (knots)
            swell_height_m: Current swell height (meters)

        Returns:
            Dictionary with:
                - level: VisibilityLevel (GOOD/MIXED/POOR)
                - confidence: 'low', 'medium', or 'high'
                - range_estimate: Estimated visibility range (e.g., '20-30m')
                - indicators: Individual indicator assessments
                - notes: Explanation of limitations
        """
        indicators = {}
        scores = []

        # Assess turbidity (if available)
        if turbidity_fnu is not None:
            turbidity_assessment = self._assess_turbidity(turbidity_fnu)
            indicators["turbidity"] = turbidity_assessment
            scores.append(turbidity_assessment["score"])

        # Assess rainfall impact
        rainfall_assessment = self._assess_rainfall(recent_rainfall_mm)
        indicators["rainfall"] = rainfall_assessment
        scores.append(rainfall_assessment["score"])

        # Assess wind/sediment impact
        wind_assessment = self._assess_wind(avg_wind_speed_kt)
        indicators["wind"] = wind_assessment
        scores.append(wind_assessment["score"])

        # Assess sea state
        swell_assessment = self._assess_swell(swell_height_m)
        indicators["swell"] = swell_assessment
        scores.append(swell_assessment["score"])

        # Calculate overall visibility
        avg_score = sum(scores) / len(scores) if scores else 0

        # Determine visibility level
        if avg_score >= 2.5:
            level = VisibilityLevel.GOOD
            range_estimate = "20-30m"
        elif avg_score >= 1.5:
            level = VisibilityLevel.MIXED
            range_estimate = "10-20m"
        else:
            level = VisibilityLevel.POOR
            range_estimate = "<10m"

        # Determine confidence
        confidence = self._calculate_confidence(turbidity_fnu, indicators)

        return {
            "level": level,
            "confidence": confidence,
            "range_estimate": range_estimate,
            "indicators": indicators,
            "notes": self._generate_notes(turbidity_fnu, confidence),
        }

    def _assess_turbidity(self, turbidity_fnu: float) -> dict[str, Any]:
        """Assess visibility based on turbidity measurement.

        Args:
            turbidity_fnu: Turbidity in FNU (Formazin Nephelometric Units)

        Returns:
            Assessment dict with value, status, score
        """
        good_threshold = self.thresholds.get("turbidity_fnu", {}).get("good", 2.0)
        poor_threshold = self.thresholds.get("turbidity_fnu", {}).get("poor", 5.0)

        if turbidity_fnu <= good_threshold:
            status = "favorable"
            score = 3  # Good
            message = f"Low turbidity ({turbidity_fnu:.2f} FNU) - clear water"
        elif turbidity_fnu <= poor_threshold:
            status = "moderate"
            score = 2  # Mixed
            message = f"Moderate turbidity ({turbidity_fnu:.2f} FNU)"
        else:
            status = "unfavorable"
            score = 1  # Poor
            message = f"High turbidity ({turbidity_fnu:.2f} FNU) - murky water"

        return {
            "value": turbidity_fnu,
            "status": status,
            "score": score,
            "message": message,
        }

    def _assess_rainfall(self, rainfall_mm: float) -> dict[str, Any]:
        """Assess visibility impact from recent rainfall.

        Args:
            rainfall_mm: Total rainfall in last 3 days

        Returns:
            Assessment dict with value, status, score
        """
        good_threshold = self.thresholds.get("rainfall_mm_3day", {}).get("good", 10)
        poor_threshold = self.thresholds.get("rainfall_mm_3day", {}).get("poor", 50)

        if rainfall_mm <= good_threshold:
            status = "favorable"
            score = 3
            message = f"Minimal rain ({rainfall_mm:.1f}mm) - no runoff impact"
        elif rainfall_mm <= poor_threshold:
            status = "moderate"
            score = 2
            message = f"Moderate rain ({rainfall_mm:.1f}mm) - some runoff"
        else:
            status = "unfavorable"
            score = 1
            message = f"Heavy rain ({rainfall_mm:.1f}mm) - significant runoff"

        return {
            "value": rainfall_mm,
            "status": status,
            "score": score,
            "message": message,
        }

    def _assess_wind(self, avg_wind_kt: float) -> dict[str, Any]:
        """Assess visibility impact from wind (sediment disturbance).

        Args:
            avg_wind_kt: 5-day rolling average wind speed

        Returns:
            Assessment dict with value, status, score
        """
        good_threshold = self.thresholds.get("wind_avg_kt_5day", {}).get("good", 8)
        poor_threshold = self.thresholds.get("wind_avg_kt_5day", {}).get("poor", 15)

        if avg_wind_kt <= good_threshold:
            status = "favorable"
            score = 3
            message = f"Calm conditions ({avg_wind_kt:.1f}kt avg) - settled sediment"
        elif avg_wind_kt <= poor_threshold:
            status = "moderate"
            score = 2
            message = f"Moderate wind ({avg_wind_kt:.1f}kt avg) - some disturbance"
        else:
            status = "unfavorable"
            score = 1
            message = f"Strong wind ({avg_wind_kt:.1f}kt avg) - churned sediment"

        return {
            "value": avg_wind_kt,
            "status": status,
            "score": score,
            "message": message,
        }

    def _assess_swell(self, swell_m: float) -> dict[str, Any]:
        """Assess visibility impact from swell (sea state).

        Args:
            swell_m: Current swell height in meters

        Returns:
            Assessment dict with value, status, score
        """
        # Calm seas = good visibility, rough seas = stirred up sediment
        if swell_m <= 0.5:
            status = "favorable"
            score = 3
            message = f"Calm seas ({swell_m:.1f}m) - minimal disturbance"
        elif swell_m <= 1.5:
            status = "moderate"
            score = 2
            message = f"Moderate swell ({swell_m:.1f}m)"
        else:
            status = "unfavorable"
            score = 1
            message = f"Rough seas ({swell_m:.1f}m) - disturbed conditions"

        return {
            "value": swell_m,
            "status": status,
            "score": score,
            "message": message,
        }

    def _calculate_confidence(
        self, turbidity_available: Optional[float], indicators: dict
    ) -> str:
        """Calculate confidence level in the estimate.

        Args:
            turbidity_available: Whether satellite turbidity data is available
            indicators: All indicator assessments

        Returns:
            Confidence level: 'low', 'medium', or 'high'
        """
        # High confidence: Have satellite turbidity data + all indicators favorable
        if turbidity_available is not None:
            favorable_count = sum(
                1 for ind in indicators.values() if ind["status"] == "favorable"
            )
            if favorable_count >= 3:
                return "high"
            else:
                return "medium"

        # Medium confidence: No turbidity but multiple favorable indicators
        favorable_count = sum(
            1 for ind in indicators.values() if ind["status"] == "favorable"
        )
        if favorable_count >= 2:
            return "medium"

        # Low confidence: Missing turbidity + mixed/poor indicators
        return "low"

    def _generate_notes(self, turbidity_available: Optional[float], confidence: str) -> str:
        """Generate explanatory notes about the estimate.

        Args:
            turbidity_available: Whether satellite data is available
            confidence: Confidence level

        Returns:
            Formatted notes string
        """
        notes = []

        if turbidity_available is None:
            notes.append("No satellite turbidity data available (cloud cover or data gap)")

        notes.append(
            "Estimate based on weather and sea state proxies - not direct measurement"
        )

        if confidence == "low":
            notes.append(
                "Low confidence - recommend checking local dive reports for actual visibility"
            )

        return ". ".join(notes) + "."
