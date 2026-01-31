"""Configuration loader for dive spots and thresholds."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from nudibranch.models import DiveSpot


class Config(BaseModel):
    """Application configuration."""

    spots: list[DiveSpot] = Field(default_factory=list)
    thresholds: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, config_dir: Path | str = "config") -> "Config":
        """Load configuration from YAML files.

        Args:
            config_dir: Directory containing spots.yaml and thresholds.yaml

        Returns:
            Loaded configuration object
        """
        config_path = Path(config_dir)

        # Load dive spots
        spots_file = config_path / "spots.yaml"
        if spots_file.exists():
            with open(spots_file) as f:
                spots_data = yaml.safe_load(f)
                spots = [DiveSpot(**spot) for spot in spots_data.get("spots", [])]
        else:
            spots = []

        # Load thresholds
        thresholds_file = config_path / "thresholds.yaml"
        if thresholds_file.exists():
            with open(thresholds_file) as f:
                thresholds_data = yaml.safe_load(f)
                thresholds = thresholds_data.get("thresholds", {})
        else:
            thresholds = {}

        return cls(spots=spots, thresholds=thresholds)
