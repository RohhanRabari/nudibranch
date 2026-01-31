"""Tests for the spot manager functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from nudibranch.tui.widgets.spot_manager import SpotManager


@pytest.fixture
def temp_config():
    """Create a temporary spots.yaml file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        initial_data = {
            "spots": [
                {
                    "name": "Test Spot 1",
                    "lat": 7.5,
                    "lng": 98.3,
                    "region": "Test Region",
                    "depth_range": "5-20m",
                    "description": "Test spot 1",
                },
                {
                    "name": "Test Spot 2",
                    "lat": 7.6,
                    "lng": 98.4,
                },
            ]
        }
        yaml.dump(initial_data, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    config_path.unlink(missing_ok=True)


def test_load_spots(temp_config):
    """Test loading spots from YAML file."""
    manager = SpotManager(temp_config)
    spots = manager.load_spots()

    assert len(spots) == 2
    assert spots[0]["name"] == "Test Spot 1"
    assert spots[0]["lat"] == 7.5
    assert spots[0]["lng"] == 98.3
    assert spots[1]["name"] == "Test Spot 2"


def test_add_spot(temp_config):
    """Test adding a new spot."""
    manager = SpotManager(temp_config)

    new_spot = {
        "name": "New Spot",
        "lat": 8.0,
        "lng": 98.5,
        "region": "New Region",
        "depth_range": "10-30m",
    }

    manager.add_spot(new_spot)

    # Reload and verify
    spots = manager.load_spots()
    assert len(spots) == 3
    assert spots[2]["name"] == "New Spot"
    assert spots[2]["lat"] == 8.0


def test_remove_spot_success(temp_config):
    """Test removing an existing spot."""
    manager = SpotManager(temp_config)

    # Remove the first spot
    result = manager.remove_spot("Test Spot 1")
    assert result is True

    # Verify it's gone
    spots = manager.load_spots()
    assert len(spots) == 1
    assert spots[0]["name"] == "Test Spot 2"


def test_remove_spot_not_found(temp_config):
    """Test removing a non-existent spot."""
    manager = SpotManager(temp_config)

    # Try to remove a spot that doesn't exist
    result = manager.remove_spot("Non-Existent Spot")
    assert result is False

    # Verify nothing changed
    spots = manager.load_spots()
    assert len(spots) == 2


def test_save_spots(temp_config):
    """Test saving spots to YAML file."""
    manager = SpotManager(temp_config)

    new_spots = [
        {
            "name": "Spot A",
            "lat": 7.7,
            "lng": 98.6,
        },
        {
            "name": "Spot B",
            "lat": 7.8,
            "lng": 98.7,
        },
    ]

    manager.save_spots(new_spots)

    # Reload and verify
    spots = manager.load_spots()
    assert len(spots) == 2
    assert spots[0]["name"] == "Spot A"
    assert spots[1]["name"] == "Spot B"


def test_load_nonexistent_file():
    """Test loading from a file that doesn't exist."""
    manager = SpotManager(Path("/tmp/nonexistent_spots.yaml"))
    spots = manager.load_spots()
    assert spots == []


def test_add_spot_minimal_fields(temp_config):
    """Test adding a spot with only required fields."""
    manager = SpotManager(temp_config)

    minimal_spot = {
        "name": "Minimal Spot",
        "lat": 7.9,
        "lng": 98.8,
    }

    manager.add_spot(minimal_spot)

    # Verify
    spots = manager.load_spots()
    assert len(spots) == 3
    assert spots[2]["name"] == "Minimal Spot"
    assert "region" not in spots[2]
    assert "depth_range" not in spots[2]


def test_spot_manager_preserves_order(temp_config):
    """Test that spot order is preserved."""
    manager = SpotManager(temp_config)

    # Add multiple spots
    manager.add_spot({"name": "Spot 3", "lat": 8.0, "lng": 98.9})
    manager.add_spot({"name": "Spot 4", "lat": 8.1, "lng": 99.0})

    spots = manager.load_spots()
    assert len(spots) == 4
    assert spots[0]["name"] == "Test Spot 1"
    assert spots[1]["name"] == "Test Spot 2"
    assert spots[2]["name"] == "Spot 3"
    assert spots[3]["name"] == "Spot 4"
