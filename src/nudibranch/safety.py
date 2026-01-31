"""Safety assessment system for freediving conditions.

Evaluates marine conditions against configurable thresholds to determine
if conditions are safe, caution-worthy, or unsafe for freediving.
"""

from typing import Any

from nudibranch.models import SafetyLevel


class SafetyAssessor:
    """Evaluates diving conditions against safety thresholds.

    Uses configurable thresholds from config/thresholds.yaml to assess
    whether conditions are safe for freediving.
    """

    def __init__(self, thresholds: dict[str, Any]) -> None:
        """Initialize the safety assessor.

        Args:
            thresholds: Threshold configuration from config file
        """
        self.thresholds = thresholds

    def assess_conditions(self, conditions: dict[str, Any]) -> dict[str, Any]:
        """Assess overall safety of diving conditions.

        Args:
            conditions: Dictionary with marine condition values:
                - wind_speed_kt: Wind speed in knots
                - wave_height_m: Wave height in meters
                - swell_height_m: Swell height in meters (optional)
                - swell_period_s: Swell period in seconds (optional)
                - wind_gust_kt: Wind gust speed in knots (optional)

        Returns:
            Dictionary with:
                - overall: Overall SafetyLevel
                - factors: Individual factor assessments
                - limiting_factor: Most restrictive condition
                - details: Human-readable explanation
        """
        factors = {}

        # Assess wind speed
        if "wind_speed_kt" in conditions:
            factors["wind"] = self._assess_metric(
                value=conditions["wind_speed_kt"],
                thresholds=self.thresholds.get("wind_speed_kt", {}),
                lower_is_better=True,
                unit="kt",
            )

        # Assess wave height
        if "wave_height_m" in conditions:
            factors["waves"] = self._assess_metric(
                value=conditions["wave_height_m"],
                thresholds=self.thresholds.get("wave_height_m", {}),
                lower_is_better=True,
                unit="m",
            )

        # Assess swell height
        if "swell_height_m" in conditions and conditions["swell_height_m"] is not None:
            factors["swell"] = self._assess_metric(
                value=conditions["swell_height_m"],
                thresholds=self.thresholds.get("swell_height_m", {}),
                lower_is_better=True,
                unit="m",
            )

        # Assess swell period (higher is better - longer period = smoother swells)
        if "swell_period_s" in conditions and conditions["swell_period_s"] is not None:
            factors["swell_period"] = self._assess_metric(
                value=conditions["swell_period_s"],
                thresholds=self.thresholds.get("swell_period_s", {}),
                lower_is_better=False,  # Higher period is better
                unit="s",
            )

        # Assess wind gusts
        if "wind_gust_kt" in conditions and conditions["wind_gust_kt"] is not None:
            factors["gusts"] = self._assess_metric(
                value=conditions["wind_gust_kt"],
                thresholds=self.thresholds.get("wind_gust_kt", {}),
                lower_is_better=True,
                unit="kt",
            )

        # Determine overall safety level (worst case)
        overall = self._determine_overall(factors)

        # Find limiting factor
        limiting_factor = self._find_limiting_factor(factors)

        return {
            "overall": overall,
            "factors": factors,
            "limiting_factor": limiting_factor,
            "details": self._generate_details(overall, factors, limiting_factor),
        }

    def _assess_metric(
        self,
        value: float,
        thresholds: dict[str, float],
        lower_is_better: bool,
        unit: str,
    ) -> dict[str, Any]:
        """Assess a single metric against thresholds.

        Args:
            value: Measured value
            thresholds: Dict with 'safe', 'caution', 'unsafe' thresholds
            lower_is_better: True if lower values are safer
            unit: Unit of measurement for display

        Returns:
            Dict with value, status, and message
        """
        safe_threshold = thresholds.get("safe", 0)
        caution_threshold = thresholds.get("caution", 0)
        unsafe_threshold = thresholds.get("unsafe", 999)

        if lower_is_better:
            # Lower values are better (wind, waves, etc.)
            if value <= safe_threshold:
                status = SafetyLevel.SAFE
                message = f"Excellent - well below {safe_threshold}{unit}"
            elif value <= caution_threshold:
                status = SafetyLevel.CAUTION
                message = f"Moderate - between {safe_threshold}-{caution_threshold}{unit}"
            else:
                status = SafetyLevel.UNSAFE
                message = f"High - exceeds {caution_threshold}{unit}"
        else:
            # Higher values are better (swell period)
            if value >= safe_threshold:
                status = SafetyLevel.SAFE
                message = f"Excellent - above {safe_threshold}{unit}"
            elif value >= caution_threshold:
                status = SafetyLevel.CAUTION
                message = f"Moderate - between {caution_threshold}-{safe_threshold}{unit}"
            else:
                status = SafetyLevel.UNSAFE
                message = f"Low - below {caution_threshold}{unit}"

        return {
            "value": value,
            "status": status,
            "message": message,
            "unit": unit,
        }

    def _determine_overall(self, factors: dict[str, dict]) -> SafetyLevel:
        """Determine overall safety level from individual factors.

        Uses worst-case approach: overall = most restrictive factor.

        Args:
            factors: Dict of individual factor assessments

        Returns:
            Overall SafetyLevel
        """
        if not factors:
            return SafetyLevel.SAFE

        # Count safety levels
        levels = [f["status"] for f in factors.values()]

        # If any factor is UNSAFE, overall is UNSAFE
        if SafetyLevel.UNSAFE in levels:
            return SafetyLevel.UNSAFE

        # If any factor is CAUTION, overall is CAUTION
        if SafetyLevel.CAUTION in levels:
            return SafetyLevel.CAUTION

        # All factors are SAFE
        return SafetyLevel.SAFE

    def _find_limiting_factor(self, factors: dict[str, dict]) -> str | None:
        """Find the most restrictive condition.

        Args:
            factors: Dict of individual factor assessments

        Returns:
            Name of limiting factor or None
        """
        if not factors:
            return None

        # Priority: UNSAFE > CAUTION > SAFE
        # Within same level, return first occurrence
        for level in [SafetyLevel.UNSAFE, SafetyLevel.CAUTION]:
            for name, assessment in factors.items():
                if assessment["status"] == level:
                    return name

        return None

    def _generate_details(
        self,
        overall: SafetyLevel,
        factors: dict[str, dict],
        limiting_factor: str | None,
    ) -> str:
        """Generate human-readable safety details.

        Args:
            overall: Overall safety level
            factors: Individual factor assessments
            limiting_factor: Name of limiting factor

        Returns:
            Formatted details string
        """
        if overall == SafetyLevel.SAFE:
            return "All conditions are within safe limits for freediving."

        if overall == SafetyLevel.CAUTION:
            if limiting_factor:
                factor = factors[limiting_factor]
                return (
                    f"Caution advised due to {limiting_factor}: "
                    f"{factor['value']}{factor['unit']} - {factor['message']}"
                )
            return "Caution advised - some conditions are marginal."

        # UNSAFE
        if limiting_factor:
            factor = factors[limiting_factor]
            return (
                f"Unsafe conditions - {limiting_factor}: "
                f"{factor['value']}{factor['unit']} - {factor['message']}"
            )
        return "Unsafe conditions detected."
