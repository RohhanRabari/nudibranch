"""Tests for the TUI application."""

import pytest
from textual.widgets import Footer, Header

from nudibranch.tui.app import (
    HeaderClock,
    NudibranchApp,
    StatusBar,
)
from nudibranch.tui.widgets.conditions_table import ConditionsTableWidget
from nudibranch.tui.widgets.tide_panel import TidePanelWidget


def test_app_initialization():
    """Test app can be initialized."""
    app = NudibranchApp()
    assert app.config is not None
    assert len(app.spots) > 0
    assert app.selected_spot is not None
    assert app.title == "Nudibranch - Dive Conditions"

    # Check that data sources are initialized
    assert app.open_meteo is not None
    assert app.tide_client is not None
    assert app.safety_assessor is not None
    assert app.visibility_estimator is not None
    assert app.aggregator is not None


def test_app_bindings():
    """Test app has correct key bindings."""
    app = NudibranchApp()

    # BINDINGS is a list of tuples (key, action, description)
    binding_keys = [b[0] for b in app.BINDINGS]
    assert "r" in binding_keys  # Refresh
    assert "q" in binding_keys  # Quit
    assert "?" in binding_keys  # Help


def test_app_has_compose_method():
    """Test app has compose method."""
    app = NudibranchApp()

    # Should have compose method
    assert hasattr(app, "compose")
    assert callable(app.compose)


def test_header_clock_updates():
    """Test header clock has update interval."""
    clock = HeaderClock()

    # Should have a method to update clock
    assert hasattr(clock, "update_clock")
    assert callable(clock.update_clock)


def test_conditions_table_widget():
    """Test conditions table widget can be created."""
    # Need spots and aggregator for initialization
    # This is a basic smoke test
    from nudibranch.aggregator import ConditionsAggregator
    from nudibranch.clients.open_meteo import OpenMeteoClient
    from nudibranch.clients.tides import TideClient
    from nudibranch.config import Config

    config = Config.load()
    spots = config.spots[:1]  # Just test with one spot

    open_meteo = OpenMeteoClient()
    tide_client = TideClient()
    aggregator = ConditionsAggregator(open_meteo, tide_client)

    table = ConditionsTableWidget(spots, aggregator)
    assert table is not None
    assert table.spots == spots
    assert table.aggregator is aggregator


def test_tide_panel_widget():
    """Test tide panel widget can be created."""
    panel = TidePanelWidget()
    assert panel is not None
    assert panel.spot_name is None
    assert panel.conditions is None


def test_status_bar_exists():
    """Test status bar exists."""
    status = StatusBar()
    assert status is not None


def test_app_loads_dive_spots():
    """Test app loads dive spots from config."""
    app = NudibranchApp()

    # Should have spots loaded from config
    assert len(app.spots) > 0

    # First spot should be selected by default
    assert app.selected_spot == app.spots[0]

    # Verify spots have required attributes
    for spot in app.spots:
        assert hasattr(spot, "name")
        assert hasattr(spot, "lat")
        assert hasattr(spot, "lng")
