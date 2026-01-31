"""Main Textual TUI application for Nudibranch dive conditions dashboard."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Label, Static

from nudibranch.aggregator import ConditionsAggregator
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient
from nudibranch.config import Config
from nudibranch.models import DiveSpot
from nudibranch.safety import SafetyAssessor
from nudibranch.tui.widgets.conditions_table import ConditionsTableWidget, RefreshComplete
from nudibranch.tui.widgets.help_screen import HelpScreen
from nudibranch.tui.widgets.spot_manager import AddSpotScreen, DeleteConfirmScreen, SpotManager
from nudibranch.tui.widgets.tide_panel import TidePanelWidget
from nudibranch.visibility import VisibilityEstimator


class HeaderClock(Static):
    """Header with title and live clock."""

    def on_mount(self) -> None:
        """Set up clock update interval."""
        self.update_clock()
        self.set_interval(1.0, self.update_clock)

    def update_clock(self) -> None:
        """Update the clock display."""
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%Y-%m-%d")
        self.update(f"🌊 NUDIBRANCH - Dive Conditions Dashboard    {date_str} {time_str}")


class ConditionsTable(Static):
    """Placeholder for conditions table widget."""

    def compose(self) -> ComposeResult:
        """Compose the table."""
        yield Label("📊 Conditions Table")
        yield Label("(Loading dive spot conditions...)")


class TidePanel(Static):
    """Placeholder for tide panel widget."""

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Label("🌙 Tide Information")
        yield Label("(Select a dive spot to see tide details)")


class StatusBar(Static):
    """Status bar showing last update and data source status."""

    def __init__(self) -> None:
        """Initialize the status bar."""
        super().__init__()
        self.last_update: Optional[datetime] = None
        self.is_refreshing = False

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        yield Label("🟢 Ready - Press 'r' to refresh data", id="status_label")

    def on_mount(self) -> None:
        """Start the status update timer."""
        self.set_interval(1.0, self.update_status)

    def update_status(self) -> None:
        """Update the status display."""
        label = self.query_one("#status_label", Label)

        if self.is_refreshing:
            label.update("⟳ Refreshing data...")
            return

        if self.last_update is None:
            label.update("🟢 Ready - Press 'r' to refresh data")
        else:
            # Calculate time since last update
            elapsed = datetime.now() - self.last_update
            seconds = int(elapsed.total_seconds())

            if seconds < 60:
                time_str = f"{seconds}s ago"
            else:
                minutes = seconds // 60
                time_str = f"{minutes}m ago"

            label.update(f"🟢 Last updated: {time_str} - Auto-refresh in {300 - seconds % 300}s")

    def set_refreshing(self, refreshing: bool) -> None:
        """Set the refreshing state."""
        self.is_refreshing = refreshing
        self.update_status()

    def mark_updated(self) -> None:
        """Mark that data was just updated."""
        self.last_update = datetime.now()
        self.is_refreshing = False
        self.update_status()


class NudibranchApp(App):
    """Nudibranch TUI application for monitoring dive conditions."""

    CSS = """
    Screen {
        background: $panel;
    }

    HeaderClock {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #main_container {
        height: 1fr;
        background: $surface;
    }

    #conditions_container {
        width: 70%;
        border: solid $primary;
        padding: 1;
    }

    #tide_container {
        width: 30%;
        border: solid $primary;
        padding: 1;
    }

    ConditionsTableWidget {
        height: 1fr;
    }

    #conditions_table {
        height: 1fr;
    }

    TidePanelWidget {
        height: 1fr;
    }

    #tide_content {
        height: 1fr;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel-darken-1;
        color: $text-muted;
        padding: 0 1;
    }

    Footer {
        background: $panel-darken-2;
    }

    /* Safety status colors */
    .safe {
        color: $success;
        text-style: bold;
    }

    .caution {
        color: $warning;
        text-style: bold;
    }

    .unsafe {
        color: $error;
        text-style: bold;
    }

    /* Visibility status colors */
    .vis-good {
        color: $success;
    }

    .vis-mixed {
        color: $warning;
    }

    .vis-poor {
        color: $error;
    }

    /* Ocean-themed highlights */
    .ocean-accent {
        color: #00CED1;
        text-style: bold;
    }

    /* Help screen */
    HelpScreen {
        align: center middle;
    }

    #help_content {
        width: 70;
        height: auto;
        max-height: 90%;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("a", "add_spot", "Add Spot"),
        ("d", "delete_spot", "Delete Spot"),
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    TITLE = "Nudibranch - Dive Conditions"

    def __init__(self) -> None:
        """Initialize the app."""
        super().__init__()
        self.config = Config.load()
        self.spots = self.config.spots
        self.selected_spot: DiveSpot | None = None if not self.spots else self.spots[0]

        # Initialize spot manager
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        spots_path = config_dir / "spots.yaml"
        self.spot_manager = SpotManager(spots_path)

        # Initialize data clients
        self.open_meteo = OpenMeteoClient()
        self.tide_client = TideClient()
        self.safety_assessor = SafetyAssessor(self.config.thresholds)
        self.visibility_estimator = VisibilityEstimator(self.config.thresholds)

        # Initialize aggregator
        self.aggregator = ConditionsAggregator(
            open_meteo=self.open_meteo,
            tide_client=self.tide_client,
            safety_assessor=self.safety_assessor,
            visibility_estimator=self.visibility_estimator,
        )

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HeaderClock()
        with Horizontal(id="main_container"):
            with Vertical(id="conditions_container"):
                yield ConditionsTableWidget(self.spots, self.aggregator)
            with Vertical(id="tide_container"):
                yield TidePanelWidget()
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.log(f"Loaded {len(self.spots)} dive spots from config")
        for spot in self.spots:
            self.log(f"  - {spot.name} ({spot.lat}, {spot.lng})")

        # Start auto-refresh timer (5 minutes)
        self.set_interval(300, self.auto_refresh)
        self.log("Auto-refresh enabled (every 5 minutes)")

    def action_refresh(self) -> None:
        """Refresh all data (manual)."""
        self.notify("Refreshing dive conditions...")
        self.log("Manual refresh requested")
        self._trigger_refresh()

    def auto_refresh(self) -> None:
        """Auto-refresh all data (periodic)."""
        self.log("Auto-refresh triggered")
        self._trigger_refresh()

    def _trigger_refresh(self) -> None:
        """Trigger a data refresh."""
        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_refreshing(True)

        # Refresh the conditions table
        table_widget = self.query_one(ConditionsTableWidget)
        table_widget.refresh_data()

    def on_refresh_complete(self, message: RefreshComplete) -> None:
        """Handle refresh completion.

        Args:
            message: Refresh complete message with counts
        """
        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.mark_updated()

        # Show notification if there were errors
        if message.error_count > 0:
            self.notify(
                f"⚠️ Refresh complete: {message.success_count} OK, {message.error_count} failed",
                severity="warning",
            )
            self.log(f"Refresh completed with {message.error_count} errors")
        else:
            self.log(f"Refresh completed successfully ({message.success_count} spots)")

    def action_help(self) -> None:
        """Show help screen."""
        self.log("Help requested")
        self.push_screen(HelpScreen())

    def action_add_spot(self) -> None:
        """Show the add spot screen."""
        self.log("Add spot requested")

        def handle_result(result: Optional[dict]) -> None:
            """Handle the result from add spot screen."""
            if result:
                # Add the spot to configuration
                self.spot_manager.add_spot(result)
                self.log(f"Added new spot: {result['name']}")
                self.notify(f"✅ Added dive spot: {result['name']}")

                # Reload spots and refresh
                self._reload_spots()

        self.push_screen(AddSpotScreen(), handle_result)

    def action_delete_spot(self) -> None:
        """Delete the currently selected spot."""
        # Get the currently selected spot
        conditions_widget = self.query_one(ConditionsTableWidget)
        table = conditions_widget.query_one(DataTable)

        if table.cursor_row is None:
            self.notify("⚠️ No spot selected", severity="warning")
            return

        # Get the spot name from the selected row
        row_key = table.get_row_at(table.cursor_row)
        if not row_key:
            return

        spot_name = str(row_key[0])  # First column is the spot name

        self.log(f"Delete spot requested: {spot_name}")

        def handle_confirm(confirmed: bool) -> None:
            """Handle the confirmation result."""
            if confirmed:
                # Remove the spot
                if self.spot_manager.remove_spot(spot_name):
                    self.log(f"Deleted spot: {spot_name}")
                    self.notify(f"🗑️ Deleted dive spot: {spot_name}")

                    # Reload spots and refresh
                    self._reload_spots()
                else:
                    self.notify("⚠️ Failed to delete spot", severity="error")

        self.push_screen(DeleteConfirmScreen(spot_name), handle_confirm)

    def _reload_spots(self) -> None:
        """Reload spots from configuration and refresh the table."""
        # Reload config
        self.config = Config.load()
        self.spots = self.config.spots

        # Update the conditions table widget with new spots
        conditions_widget = self.query_one(ConditionsTableWidget)
        conditions_widget.update_spots(self.spots)

        # Clear the tide panel
        tide_panel = self.query_one(TidePanelWidget)
        tide_panel.clear()

        # Trigger a refresh to fetch data for new/remaining spots
        self._trigger_refresh()

        self.log(f"Reloaded {len(self.spots)} spots from config")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row selection in the conditions table.

        Args:
            event: Row highlighted event
        """
        # Get the conditions table widget
        conditions_widget = self.query_one(ConditionsTableWidget)
        tide_panel = self.query_one(TidePanelWidget)

        # Get selected spot name from event
        spot_name = str(event.row_key.value)

        if spot_name:
            # Get conditions for this spot
            conditions = conditions_widget.get_conditions(spot_name)

            if conditions:
                # Update tide panel
                tide_panel.set_conditions(spot_name, conditions)
                self.log(f"Selected spot: {spot_name}")
            else:
                self.log(f"No conditions available for {spot_name}")
                tide_panel.clear()


def main() -> None:
    """Entry point for the TUI application."""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    app = NudibranchApp()
    app.run()


if __name__ == "__main__":
    main()
