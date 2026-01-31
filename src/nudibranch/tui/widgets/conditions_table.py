"""Conditions table widget for displaying multi-spot dive conditions."""

import asyncio
from datetime import datetime
from typing import Optional

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Static

from nudibranch.aggregator import ConditionsAggregator
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient
from nudibranch.models import DiveSpot, FullConditions, SafetyLevel, VisibilityLevel
from nudibranch.safety import SafetyAssessor
from nudibranch.visibility import VisibilityEstimator


class ConditionsTableWidget(Static):
    """Widget displaying conditions for multiple dive spots in a table."""

    def __init__(
        self,
        spots: list[DiveSpot],
        aggregator: ConditionsAggregator,
    ) -> None:
        """Initialize the conditions table.

        Args:
            spots: List of dive spots to monitor
            aggregator: Conditions aggregator for fetching data
        """
        super().__init__()
        self.spots = spots
        self.aggregator = aggregator
        self.conditions_cache: dict[str, FullConditions] = {}
        self.is_loading = False

    def compose(self) -> ComposeResult:
        """Compose the table widget."""
        table = DataTable(id="conditions_table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        yield table

    def on_mount(self) -> None:
        """Set up the table when mounted."""
        table = self.query_one(DataTable)

        # Add columns with explicit widths to fit more data
        table.add_column("Spot", key="spot", width=15)
        table.add_column("Waves", key="waves", width=11)
        table.add_column("Wind", key="wind", width=10)
        table.add_column("Swell", key="swell", width=11)
        table.add_column("Tide", key="tide", width=14)
        table.add_column("Vis", key="visibility", width=8)
        table.add_column("Status", key="status", width=10)

        # Add placeholder rows
        for spot in self.spots:
            self._add_loading_row(spot.name)

        # Start loading data
        self.refresh_data()

    def _add_loading_row(self, spot_name: str) -> None:
        """Add a loading placeholder row."""
        table = self.query_one(DataTable)
        table.add_row(
            Text(spot_name, style="bold"),
            Text("Loading...", style="dim italic"),
            Text("Loading...", style="dim italic"),
            Text("Loading...", style="dim italic"),
            Text("Loading...", style="dim italic"),
            Text("Loading...", style="dim italic"),
            Text("Loading...", style="dim italic"),
            key=spot_name,
        )

    @work(exclusive=True)
    async def refresh_data(self) -> None:
        """Refresh conditions data for all spots."""
        if self.is_loading:
            return

        self.is_loading = True
        table = self.query_one(DataTable)

        success_count = 0
        error_count = 0

        # Fetch all spots in parallel for better performance
        async def fetch_spot_safe(spot: DiveSpot) -> tuple[DiveSpot, Optional[FullConditions], Optional[Exception]]:
            """Fetch conditions for a spot, catching exceptions."""
            try:
                conditions = await self.aggregator.fetch_spot_conditions(spot)
                return spot, conditions, None
            except Exception as e:
                return spot, None, e

        # Fetch all spots concurrently
        results = await asyncio.gather(*[fetch_spot_safe(spot) for spot in self.spots])

        # Process results
        for spot, conditions, error in results:
            if error:
                self.log.error(f"Failed to fetch conditions for {spot.name}: {error}")
                # Keep old data if available, otherwise show error
                if spot.name not in self.conditions_cache:
                    self._update_row_error(spot.name)
                error_count += 1
            else:
                self.conditions_cache[spot.name] = conditions
                self._update_row(spot.name, conditions)
                success_count += 1

        self.is_loading = False

        # Post refresh complete message
        if error_count > 0:
            self.post_message(RefreshComplete(success_count, error_count))
        else:
            self.post_message(RefreshComplete(success_count, 0))

    def _update_row(self, spot_name: str, conditions: FullConditions) -> None:
        """Update a row with actual conditions data."""
        table = self.query_one(DataTable)

        # Format waves
        if conditions.marine:
            waves_text = (
                f"{conditions.marine.wave_height_m:.1f}m "
                f"@ {conditions.marine.wave_period_s or 0:.0f}s"
            )
        else:
            waves_text = "N/A"

        # Format wind
        if conditions.marine:
            wind_kt = conditions.marine.wind_speed_kt
            wind_dir = conditions.marine.wind_direction_deg or 0
            direction = self._degrees_to_cardinal(wind_dir)
            wind_text = f"{wind_kt:.0f}kt {direction}"
        else:
            wind_text = "N/A"

        # Format swell
        if conditions.marine and conditions.marine.swell_height_m:
            swell_text = (
                f"{conditions.marine.swell_height_m:.1f}m "
                f"@ {conditions.marine.swell_period_s or 0:.0f}s"
            )
        else:
            swell_text = "N/A"

        # Format tide
        if conditions.tides:
            if conditions.tides.is_rising:
                arrow = "↑"
                next_event = conditions.tides.next_high
                event_type = "High"
            else:
                arrow = "↓"
                next_event = conditions.tides.next_low
                event_type = "Low"

            if next_event:
                time_str = next_event.time.strftime("%I:%M %p")
                tide_text = f"{arrow} → {event_type} {time_str}"
            else:
                tide_text = f"{arrow} {event_type}"
        else:
            tide_text = "N/A"

        # Format visibility
        if conditions.visibility:
            level = conditions.visibility.level
            if level == VisibilityLevel.GOOD:
                vis_text = Text("🟢 Good", style="green bold")
            elif level == VisibilityLevel.MIXED:
                vis_text = Text("🟡 Mixed", style="yellow bold")
            else:
                vis_text = Text("🔴 Poor", style="red bold")
        else:
            vis_text = Text("? Unknown", style="dim")

        # Format safety status
        if conditions.safety:
            status = conditions.safety.overall
            if status == SafetyLevel.SAFE:
                status_text = Text("✓ SAFE", style="green bold")
            elif status == SafetyLevel.CAUTION:
                status_text = Text("⚠ CAUTION", style="yellow bold")
            else:
                status_text = Text("✗ UNSAFE", style="red bold")
        else:
            status_text = Text("? Unknown", style="dim")

        # Update the row
        table.update_cell(spot_name, "spot", Text(spot_name, style="bold"))
        table.update_cell(spot_name, "waves", Text(waves_text))
        table.update_cell(spot_name, "wind", Text(wind_text))
        table.update_cell(spot_name, "swell", Text(swell_text))
        table.update_cell(spot_name, "tide", Text(tide_text))
        table.update_cell(spot_name, "visibility", vis_text)
        table.update_cell(spot_name, "status", status_text)

    def _update_row_error(self, spot_name: str) -> None:
        """Update a row with error state."""
        table = self.query_one(DataTable)
        error_text = Text("Error", style="red italic")

        table.update_cell(spot_name, "spot", Text(spot_name, style="bold"))
        table.update_cell(spot_name, "waves", error_text)
        table.update_cell(spot_name, "wind", error_text)
        table.update_cell(spot_name, "swell", error_text)
        table.update_cell(spot_name, "tide", error_text)
        table.update_cell(spot_name, "visibility", error_text)
        table.update_cell(spot_name, "status", error_text)

    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert degrees to cardinal direction.

        Args:
            degrees: Wind direction in degrees (0-360)

        Returns:
            Cardinal direction (N, NE, E, SE, S, SW, W, NW)
        """
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]

    def get_selected_spot(self) -> Optional[str]:
        """Get the currently selected spot name.

        Returns:
            Name of selected spot, or None if no selection
        """
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            # Get the row key from the coordinate
            row = table.get_row_at(table.cursor_row)
            # The row key is the spot name we used when adding the row
            return str(row)
        return None

    def get_conditions(self, spot_name: str) -> Optional[FullConditions]:
        """Get cached conditions for a spot.

        Args:
            spot_name: Name of the dive spot

        Returns:
            FullConditions if available, None otherwise
        """
        return self.conditions_cache.get(spot_name)

    def update_spots(self, spots: list[DiveSpot]) -> None:
        """Update the list of spots and rebuild the table.

        Args:
            spots: New list of dive spots to monitor
        """
        self.spots = spots
        self.conditions_cache.clear()

        # Clear and rebuild the table
        table = self.query_one(DataTable)
        table.clear()

        # Add loading rows for all spots
        for spot in self.spots:
            self._add_loading_row(spot.name)

        # Refresh data for new spots
        self.refresh_data()


class RefreshComplete(Message):
    """Message posted when data refresh completes."""

    def __init__(self, success_count: int, error_count: int) -> None:
        """Initialize the message.

        Args:
            success_count: Number of successful fetches
            error_count: Number of failed fetches
        """
        super().__init__()
        self.success_count = success_count
        self.error_count = error_count
